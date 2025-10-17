"""V2.2 Campaign Worker - Dual-lane background sender.

This worker runs continuously and sends messages across all domains
using the dual-lane (alias-based) priority queue system.

In production, this should run as:
- Celery task (recommended)
- Separate process with APScheduler
- Kubernetes CronJob (every minute)
"""
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from loguru import logger

from app.services.campaign_scheduler import campaign_scheduler, DOMAINS
from app.services.email_sender import email_sender  # Use unified email sender
from app.services.store_factory import leads_store
from app.services.template_renderer import TemplateRenderer


class CampaignWorker:
    """Background worker for sending campaign messages using dual-lane queue."""
    
    def __init__(self):
        self.email_sender = email_sender  # Use unified email sender (handles HTML, images, PDFs, signatures)
        self.renderer = TemplateRenderer()
        self.running = False
    
    async def run_once(self) -> dict:
        """Execute one iteration of the worker (check all domains).
        
        Production-ready lifecycle management:
        1. Activate scheduled campaigns (draft → active)
        2. Process and send due messages
        3. Complete finished campaigns (active → completed)
        
        Returns:
            Dict with statistics about this run
        """
        current_time = datetime.now(ZoneInfo("Europe/Amsterdam"))
        stats = {
            "timestamp": current_time.isoformat(),
            "campaigns_activated": 0,
            "campaigns_completed": 0,
            "domains_checked": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "by_domain": {}
        }
        
        logger.info(f"📊 Worker run at {current_time}")
        
        # PHASE 1: Activate scheduled campaigns that reached their start_at time
        activated_count = await self._activate_scheduled_campaigns(current_time)
        stats["campaigns_activated"] = activated_count
        
        # PHASE 2: Process and send due messages for each domain
        for domain in DOMAINS:
            domain_stats = await self._process_domain(domain, current_time)
            stats["domains_checked"] += 1
            stats["messages_sent"] += domain_stats["sent"]
            stats["messages_failed"] += domain_stats["failed"]
            stats["by_domain"][domain] = domain_stats
        
        # PHASE 3: Complete campaigns that have finished
        completed_count = await self._complete_finished_campaigns()
        stats["campaigns_completed"] = completed_count
        
        logger.info(
            f"✅ Worker completed: "
            f"{stats['campaigns_activated']} activated, "
            f"{stats['messages_sent']} sent, "
            f"{stats['messages_failed']} failed, "
            f"{stats['campaigns_completed']} completed"
        )
        
        return stats
    
    async def _process_domain(self, domain: str, current_time: datetime) -> dict:
        """Process one domain - get and send dual-lane messages.
        
        Args:
            domain: Domain to process
            current_time: Current timestamp
            
        Returns:
            Dict with sent/failed counts
        """
        stats = {"sent": 0, "failed": 0, "messages": []}
        
        # Get next messages for this domain (dual-lane selection)
        messages = campaign_scheduler.get_next_messages_to_send(domain, current_time)
        
        if not messages:
            logger.debug(f"No messages due for {domain}")
            return stats
        
        logger.info(f"Processing {len(messages)} messages for {domain}")
        
        # Send each message
        for message in messages:
            success = await self._send_message(message)
            
            if success:
                stats["sent"] += 1
                stats["messages"].append({
                    "id": message.id,
                    "lead_id": message.lead_id,
                    "mail_number": message.mail_number,
                    "alias": message.alias,
                    "status": "sent"
                })
            else:
                stats["failed"] += 1
                stats["messages"].append({
                    "id": message.id,
                    "lead_id": message.lead_id,
                    "mail_number": message.mail_number,
                    "alias": message.alias,
                    "status": "failed"
                })
        
        return stats
    
    async def _send_message(self, message) -> bool:
        """Send a single message.
        
        Args:
            message: Message object to send
            
        Returns:
            True if sent successfully
        """
        try:
            # Get lead
            lead = leads_store.get_by_id(message.lead_id)
            if not lead:
                logger.error(f"Lead {message.lead_id} not found for message {message.id}")
                
                # Mark as failed
                from app.services.store_factory import campaigns_store
                from app.models.message import MessageStatus
                campaigns_store.update_message_status(message.id, MessageStatus.failed, error="Lead not found")
                
                return False
            
            # V2.2: Check stop criteria BEFORE sending
            if leads_store.is_stopped(lead.id):
                logger.warning(f"Lead {lead.id} is stopped, canceling future messages")
                
                # Cancel all future messages for this lead
                from app.services.campaign_scheduler import campaign_scheduler
                from app.models.message import MessageStatus
                canceled = campaign_scheduler.cancel_future_messages(
                    lead.id, 
                    message.mail_number
                )
                
                logger.info(f"Canceled {canceled} future messages for stopped lead {lead.id}")
                
                # Mark THIS message as canceled too
                from app.services.store_factory import campaigns_store
                campaigns_store.update_message_status(message.id, MessageStatus.canceled, error="Lead is stopped")
                
                return False
            
            # Get campaign to find template
            from app.services.store_factory import campaigns_store as campaign_store
            from app.models.campaign import CampaignStatus
            
            campaign = campaign_store.get_campaign(message.campaign_id)
            if not campaign:
                logger.error(f"Campaign {message.campaign_id} not found")
                
                # Mark as failed
                from app.models.message import MessageStatus
                campaigns_store.update_message_status(message.id, MessageStatus.failed, error="Campaign not found")
                
                return False
            
            # V2.2: Check campaign status (draft/paused/deleted guard)
            if campaign.status in [CampaignStatus.draft, CampaignStatus.paused, CampaignStatus.deleted]:
                logger.info(f"Campaign {campaign.id} is {campaign.status}, skipping message {message.id}")
                
                # Mark as canceled
                from app.models.message import MessageStatus
                campaigns_store.update_message_status(message.id, MessageStatus.canceled, error=f"Campaign is {campaign.status}")
                
                return False
            
            # V2.2: Get template from MESSAGE (not campaign!)
            # Each message has its own template_id (e.g., v1m1, v1m2, v1m3, v1m4)
            # Use SAME template source as testsend (hybrid_template_service)
            from app.services.hybrid_template_service import hybrid_template_service
            from app.core.template_id_normalizer import normalize_template_id
            
            # Normalize template_id: v1m1 -> v1_mail1 (same as testsend!)
            normalized_id = normalize_template_id(message.template_id)
            
            template = hybrid_template_service.get_template(normalized_id)
            if not template:
                logger.error(f"Template {message.template_id} (normalized: {normalized_id}) not found for message {message.id} (mail #{message.mail_number})")
                
                # Mark as failed
                from app.services.store_factory import campaigns_store
                from app.models.message import MessageStatus
                campaigns_store.update_message_status(message.id, MessageStatus.failed, error=f"Template {normalized_id} not found")
                
                return False
            
            logger.debug(f"Using template {normalized_id} for message {message.id}")
            
            # Render template with lead variables (HardCodedTemplate has .body and .subject, not _template)
            # Prepare context (renderer.render() expects dict with 'lead', 'vars', etc.)
            context = {
                'lead': {
                    'id': lead.id,
                    'email': lead.email,
                    'company': lead.company,
                    'url': lead.url,
                    'image_key': lead.image_key if hasattr(lead, 'image_key') else None
                },
                'vars': lead.vars if hasattr(lead, 'vars') else {},
                'campaign': {'id': campaign.id, 'name': campaign.name},
                'domain': message.domain_used
            }
            
            # renderer.render() returns (rendered_text, warnings)
            html_body, body_warnings = self.renderer.render(template.body, context)
            text_body = template.body  # Plain text fallback
            subject, subject_warnings = self.renderer.render(template.subject, context)
            
            if body_warnings:
                logger.warning(f"Template rendering warnings: {body_warnings}")
            if subject_warnings:
                logger.warning(f"Subject rendering warnings: {subject_warnings}")
            
            # Get lead assets (screenshot + report)
            image_key = lead.image_key if hasattr(lead, 'image_key') else None
            report_filename = None
            if hasattr(lead, 'vars') and isinstance(lead.vars, dict):
                report_filename = lead.vars.get('report_filename')
            
            # Send via unified email_sender (same as testsend - with HTML, images, PDFs, signatures!)
            result = await self.email_sender.send_email(
                to_email=lead.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                version=message.template_version,
                mail_number=message.mail_number,
                lead_id=lead.id,
                message_id=message.id,
                image_key=image_key,
                report_filename=report_filename,
                enable_tracking=True  # Enable tracking pixel + unsubscribe headers
            )
            
            # CRITICAL: Mark message as sent to prevent re-sending!
            if result.get('success', False):
                from app.services.store_factory import campaigns_store
                from app.models.message import MessageStatus
                campaigns_store.update_message_status(message.id, MessageStatus.sent)
                logger.debug(f"✅ Message {message.id} marked as sent")
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error sending message {message.id}: {str(e)}")
            
            # CRITICAL: Mark message as failed to prevent infinite retry
            from app.services.store_factory import campaigns_store
            from app.models.message import MessageStatus
            campaigns_store.update_message_status(message.id, MessageStatus.failed, error=str(e))
            
            return False
    
    async def _activate_scheduled_campaigns(self, current_time: datetime) -> int:
        """
        Activate draft campaigns that have reached their start_at time.
        
        Production-ready implementation:
        - Checks all draft campaigns with start_at set
        - Activates if current_time >= start_at
        - Logs status transitions
        - Returns count of activated campaigns
        
        Args:
            current_time: Current time in Europe/Amsterdam timezone
            
        Returns:
            Number of campaigns activated
        """
        from app.services.store_factory import campaigns_store
        from app.models.campaign import CampaignStatus
        
        try:
            # Get all schedulable draft campaigns
            schedulable = campaigns_store.get_schedulable_draft_campaigns(current_time)
            
            if not schedulable:
                logger.debug("No draft campaigns ready for activation")
                return 0
            
            activated_count = 0
            for campaign in schedulable:
                success = campaigns_store.update_campaign_status(
                    campaign.id,
                    CampaignStatus.active,
                    reason=f"Start time reached (scheduled: {campaign.start_at})"
                )
                
                if success:
                    activated_count += 1
                    logger.info(
                        f"🚀 Activated campaign {campaign.id}: {campaign.name} "
                        f"(scheduled for {campaign.start_at})"
                    )
            
            if activated_count > 0:
                logger.info(f"✅ Activated {activated_count} scheduled campaign(s)")
            
            return activated_count
            
        except Exception as e:
            logger.error(f"Error activating scheduled campaigns: {str(e)}")
            return 0
    
    async def _complete_finished_campaigns(self) -> int:
        """
        Mark active campaigns as completed when all messages are in final state.
        
        Production-ready implementation:
        - Checks all active campaigns
        - Verifies all messages are sent/failed/bounced/canceled
        - Marks campaign as completed
        - Logs completion statistics
        - Returns count of completed campaigns
        
        Returns:
            Number of campaigns completed
        """
        from app.services.store_factory import campaigns_store
        from app.models.campaign import CampaignStatus
        
        try:
            # Get all completable active campaigns
            completable = campaigns_store.get_completable_active_campaigns()
            
            if not completable:
                logger.debug("No active campaigns ready for completion")
                return 0
            
            completed_count = 0
            for campaign in completable:
                # Get campaign KPIs for completion summary
                kpis = campaigns_store.get_campaign_kpis(campaign.id)
                
                success = campaigns_store.update_campaign_status(
                    campaign.id,
                    CampaignStatus.completed,
                    reason=f"All messages finished ({kpis.total_sent}/{kpis.total_planned} sent)"
                )
                
                if success:
                    completed_count += 1
                    logger.info(
                        f"🎉 Completed campaign {campaign.id}: {campaign.name} "
                        f"(sent: {kpis.total_sent}/{kpis.total_planned}, "
                        f"opened: {kpis.total_opened}, "
                        f"failed: {kpis.total_failed})"
                    )
            
            if completed_count > 0:
                logger.info(f"✅ Completed {completed_count} campaign(s)")
            
            return completed_count
            
        except Exception as e:
            logger.error(f"Error completing finished campaigns: {str(e)}")
            return 0
    
    async def run_continuous(self, interval_seconds: int = 60):
        """Run worker continuously with specified interval.
        
        Args:
            interval_seconds: Seconds between runs (default 60 = 1 minute)
        """
        self.running = True
        logger.info(f"Starting continuous worker with {interval_seconds}s interval")
        
        while self.running:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
            
            # Wait for next interval
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Stop the continuous worker."""
        self.running = False
        logger.info("Worker stopped")


# Global worker instance
campaign_worker = CampaignWorker()
