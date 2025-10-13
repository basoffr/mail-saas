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
from app.services.message_sender import MessageSender
from app.services.leads_store import leads_store
from app.services.template_renderer import TemplateRenderer


class CampaignWorker:
    """Background worker for sending campaign messages using dual-lane queue."""
    
    def __init__(self):
        self.sender = MessageSender()
        self.renderer = TemplateRenderer()
        self.running = False
    
    async def run_once(self) -> dict:
        """Execute one iteration of the worker (check all domains).
        
        Returns:
            Dict with statistics about this run
        """
        current_time = datetime.now(ZoneInfo("Europe/Amsterdam"))
        stats = {
            "timestamp": current_time.isoformat(),
            "domains_checked": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "by_domain": {}
        }
        
        logger.info(f"Worker run at {current_time}")
        
        # Check each domain for due messages
        for domain in DOMAINS:
            domain_stats = await self._process_domain(domain, current_time)
            stats["domains_checked"] += 1
            stats["messages_sent"] += domain_stats["sent"]
            stats["messages_failed"] += domain_stats["failed"]
            stats["by_domain"][domain] = domain_stats
        
        logger.info(
            f"Worker completed: {stats['messages_sent']} sent, "
            f"{stats['messages_failed']} failed across {stats['domains_checked']} domains"
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
            lead = leads_store.get(message.lead_id)
            if not lead:
                logger.error(f"Lead {message.lead_id} not found for message {message.id}")
                return False
            
            # V2.2: Check stop criteria BEFORE sending
            if leads_store.is_stopped(lead.id):
                logger.warning(f"Lead {lead.id} is stopped, canceling future messages")
                
                # Cancel all future messages for this lead
                from app.services.campaign_scheduler import campaign_scheduler
                canceled = campaign_scheduler.cancel_future_messages(
                    lead.id, 
                    message.mail_number
                )
                
                logger.info(f"Canceled {canceled} future messages for stopped lead {lead.id}")
                return False
            
            # Get campaign to find template
            from app.services.campaign_store import campaign_store
            campaign = campaign_store.get_campaign(message.campaign_id)
            if not campaign:
                logger.error(f"Campaign {message.campaign_id} not found")
                return False
            
            # Render template
            from app.services.template_store import template_store
            template = template_store.get(campaign.template_id)
            if not template:
                logger.error(f"Template {campaign.template_id} not found")
                return False
            
            rendered_content = self.renderer.render(template.body, lead)
            
            # Send via MessageSender
            success = await self.sender.send_message(message, lead, rendered_content)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending message {message.id}: {str(e)}")
            return False
    
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
