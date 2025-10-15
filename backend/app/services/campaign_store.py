import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from loguru import logger

from app.models.campaign import Campaign, CampaignAudience, Message, MessageEvent, CampaignStatus, MessageStatus
from app.schemas.campaign import CampaignQuery, MessageQuery, CampaignKPIs, TimelinePoint


class CampaignStore:
    """In-memory storage for campaigns (MVP implementation)."""
    
    def __init__(self):
        self.campaigns: Dict[str, Campaign] = {}
        self.audiences: Dict[str, CampaignAudience] = {}
        self.messages: Dict[str, Message] = {}
        self.events: Dict[str, MessageEvent] = {}
    
    def create_campaign(self, campaign: Campaign) -> Campaign:
        """Create a new campaign."""
        self.campaigns[campaign.id] = campaign
        logger.info(f"Created campaign {campaign.id}: {campaign.name}")
        return campaign
    
    def duplicate_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Duplicate an existing campaign with new ID and reset status."""
        original = self.campaigns.get(campaign_id)
        if not original:
            logger.warning(f"Campaign {campaign_id} not found for duplication")
            return None
        
        # Create new campaign with copied attributes
        new_id = str(uuid.uuid4())
        duplicate = Campaign(
            id=new_id,
            name=f"{original.name} (Copy)",
            template_id=original.template_id,
            domain=original.domain,
            status=CampaignStatus.draft,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            start_at=None,  # Reset start date
            # Copy follow-up settings
            followup_enabled=original.followup_enabled,
            followup_days=original.followup_days,
            followup_attach_report=original.followup_attach_report
        )
        
        # Save duplicate
        self.campaigns[new_id] = duplicate
        logger.info(f"Duplicated campaign {campaign_id} to {new_id}: {duplicate.name}")
        
        # Copy audience if exists
        for audience_id, audience in self.audiences.items():
            if audience.campaign_id == campaign_id:
                new_audience = CampaignAudience(
                    id=str(uuid.uuid4()),
                    campaign_id=new_id,
                    lead_ids=audience.lead_ids.copy(),  # Copy lead IDs
                    exclude_suppressed=audience.exclude_suppressed,
                    exclude_recent_days=audience.exclude_recent_days,
                    one_per_domain=audience.one_per_domain,
                    created_at=datetime.utcnow()
                )
                self.audiences[new_audience.id] = new_audience
                logger.info(f"Duplicated audience with {len(new_audience.lead_ids)} leads")
                break
        
        return duplicate
    
    def check_domain_busy(self, domain: str) -> bool:
        """Check if domain has an active campaign running."""
        active_statuses = {CampaignStatus.running}
        
        for campaign in self.campaigns.values():
            if (hasattr(campaign, 'domain') and campaign.domain == domain and 
                campaign.status in active_statuses):
                return True
        return False
    
    def get_active_campaigns_by_domain(self) -> Dict[str, List[Campaign]]:
        """Get all active campaigns grouped by domain."""
        active_statuses = {CampaignStatus.running}
        domain_campaigns = {}
        
        for campaign in self.campaigns.values():
            if (hasattr(campaign, 'domain') and campaign.status in active_statuses):
                domain = campaign.domain
                if domain not in domain_campaigns:
                    domain_campaigns[domain] = []
                domain_campaigns[domain].append(campaign)
        
        return domain_campaigns
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages for CSV export."""
        return list(self.messages.values())
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        return self.campaigns.get(campaign_id)
    
    def list_campaigns(self, query: CampaignQuery) -> tuple[List[Campaign], int]:
        """List campaigns with filtering and pagination."""
        campaigns = list(self.campaigns.values())
        
        # Apply filters
        if query.status:
            campaigns = [c for c in campaigns if c.status in query.status]
        
        if query.search:
            search_lower = query.search.lower()
            campaigns = [c for c in campaigns if search_lower in c.name.lower()]
        
        if query.date_from:
            campaigns = [c for c in campaigns if c.created_at >= query.date_from]
        
        if query.date_to:
            campaigns = [c for c in campaigns if c.created_at <= query.date_to]
        
        # Sort by created_at desc
        campaigns.sort(key=lambda c: c.created_at, reverse=True)
        
        total = len(campaigns)
        
        # Apply pagination
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        campaigns = campaigns[start:end]
        
        return campaigns, total
    
    def update_campaign_status(self, campaign_id: str, status: CampaignStatus, reason: str = None) -> bool:
        """
        Update campaign status with validation and logging.
        
        Args:
            campaign_id: Campaign ID
            status: New status
            reason: Optional reason for status change
            
        Returns:
            True if updated successfully
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            logger.warning(f"Cannot update status: campaign {campaign_id} not found")
            return False
        
        old_status = campaign.status
        campaign.status = status
        campaign.updated_at = datetime.utcnow()
        
        log_msg = f"Campaign {campaign_id} status: {old_status} → {status}"
        if reason:
            log_msg += f" (reason: {reason})"
        logger.info(log_msg)
        
        return True
    
    def get_campaigns_by_status(self, status: CampaignStatus) -> List[Campaign]:
        """Get all campaigns with specific status."""
        return [c for c in self.campaigns.values() if c.status == status]
    
    def get_schedulable_draft_campaigns(self, current_time: datetime) -> List[Campaign]:
        """
        Get draft campaigns that should be activated.
        
        Returns campaigns where:
        - status = draft
        - start_at is set
        - start_at <= current_time
        """
        return [
            c for c in self.campaigns.values()
            if c.status == CampaignStatus.draft
            and c.start_at is not None
            and c.start_at <= current_time
        ]
    
    def get_completable_active_campaigns(self) -> List[Campaign]:
        """
        Get active campaigns that should be marked as completed.
        
        Returns campaigns where:
        - status = active
        - all messages are in final state (sent/failed/bounced/canceled)
        """
        completable = []
        
        for campaign in self.campaigns.values():
            if campaign.status != CampaignStatus.active:
                continue
            
            # Get all messages for this campaign
            campaign_messages = [
                m for m in self.messages.values()
                if m.campaign_id == campaign.id
            ]
            
            if not campaign_messages:
                continue
            
            # Check if all messages are in final state
            final_statuses = {
                MessageStatus.sent,
                MessageStatus.opened,
                MessageStatus.failed,
                MessageStatus.bounced,
                MessageStatus.canceled
            }
            
            all_final = all(m.status in final_statuses for m in campaign_messages)
            
            if all_final:
                completable.append(campaign)
        
        return completable
    
    def create_audience(self, audience: CampaignAudience) -> CampaignAudience:
        """Create campaign audience snapshot."""
        self.audiences[audience.id] = audience
        return audience
    
    def get_audience(self, campaign_id: str) -> Optional[CampaignAudience]:
        """Get audience for campaign."""
        for audience in self.audiences.values():
            if audience.campaign_id == campaign_id:
                return audience
        return None
    
    def create_messages(self, messages: List[Message]) -> List[Message]:
        """Create multiple messages."""
        for message in messages:
            self.messages[message.id] = message
        logger.info(f"Created {len(messages)} messages")
        return messages
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID."""
        return self.messages.get(message_id)
    
    def list_messages(self, query: MessageQuery) -> tuple[List[Message], int]:
        """List messages with filtering and pagination."""
        messages = list(self.messages.values())
        
        # Apply filters
        if query.campaign_id:
            messages = [m for m in messages if m.campaign_id == query.campaign_id]
        
        if query.status:
            messages = [m for m in messages if m.status in query.status]
        
        if query.lead_id:
            messages = [m for m in messages if m.lead_id == query.lead_id]
        
        # Sort by scheduled_at
        messages.sort(key=lambda m: m.scheduled_at)
        
        total = len(messages)
        
        # Apply pagination
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        messages = messages[start:end]
        
        return messages, total
    
    def update_message_status(self, message_id: str, status: MessageStatus, error: str = None) -> bool:
        """Update message status."""
        message = self.messages.get(message_id)
        if not message:
            return False
        
        message.status = status
        if status == MessageStatus.sent:
            message.sent_at = datetime.utcnow()
        elif error:
            message.last_error = error
        
        return True
    
    def create_event(self, event: MessageEvent) -> MessageEvent:
        """Create message event."""
        self.events[event.id] = event
        return event
    
    def get_campaign_kpis(self, campaign_id: str) -> CampaignKPIs:
        """Calculate campaign KPIs."""
        campaign_messages = [m for m in self.messages.values() if m.campaign_id == campaign_id]
        
        total_planned = len(campaign_messages)
        total_sent = len([m for m in campaign_messages if m.status == MessageStatus.sent])
        total_opened = len([m for m in campaign_messages if m.status == MessageStatus.opened])
        total_failed = len([m for m in campaign_messages if m.status == MessageStatus.failed])
        
        open_rate = (total_opened / total_sent) if total_sent > 0 else 0.0
        
        # Calculate average tempo (simplified)
        avg_tempo_per_hour = 0.0
        if campaign_messages:
            # Estimate based on throttle settings
            avg_tempo_per_hour = 3.0  # 1 email per 20 min = 3 per hour per domain
        
        return CampaignKPIs(
            total_planned=total_planned,
            total_sent=total_sent,
            total_opened=total_opened,
            total_failed=total_failed,
            open_rate=open_rate,
            avg_tempo_per_hour=avg_tempo_per_hour
        )
    
    def get_campaign_timeline(self, campaign_id: str) -> List[TimelinePoint]:
        """Get campaign timeline data."""
        campaign_messages = [m for m in self.messages.values() if m.campaign_id == campaign_id]
        
        # Group by date
        daily_stats: Dict[str, Dict[str, int]] = {}
        
        for message in campaign_messages:
            if message.sent_at:
                date_key = message.sent_at.strftime("%Y-%m-%d")
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"sent": 0, "opened": 0}
                
                daily_stats[date_key]["sent"] += 1
                
                if message.status == MessageStatus.opened:
                    daily_stats[date_key]["opened"] += 1
        
        # Convert to timeline points
        timeline = []
        for date, stats in sorted(daily_stats.items()):
            timeline.append(TimelinePoint(
                date=date,
                sent=stats["sent"],
                opened=stats["opened"]
            ))
        
        return timeline
    
    def soft_delete_campaign(self, campaign_id: str) -> bool:
        """V2.2: Soft delete campaign and cancel future messages."""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return False
        
        # Update campaign status
        campaign.status = CampaignStatus.deleted
        campaign.deleted_at = datetime.utcnow()
        
        # Cancel all queued future messages
        now = datetime.utcnow()
        canceled_count = 0
        
        for message in self.messages.values():
            if (message.campaign_id == campaign_id and 
                message.status == MessageStatus.queued and
                message.scheduled_at > now):
                
                message.status = MessageStatus.canceled
                message.cancel_reason = "campaign_deleted"
                canceled_count += 1
        
        logger.info(f"Soft deleted campaign {campaign_id}, canceled {canceled_count} future messages")
        return True
    
    def pause_campaign(self, campaign_id: str) -> bool:
        """V2.2: Pause campaign (messages stay queued but won't send)."""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return False
        
        campaign.status = CampaignStatus.paused
        campaign.paused_at = datetime.utcnow()
        
        logger.info(f"Paused campaign {campaign_id}")
        return True
    
    def resume_campaign(self, campaign_id: str) -> bool:
        """V2.2: Resume paused campaign."""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return False
        
        if campaign.status == CampaignStatus.paused:
            campaign.status = CampaignStatus.active
            campaign.paused_at = None
            logger.info(f"Resumed campaign {campaign_id}")
            return True
        
        return False
    
    def stop_lead_flow(self, campaign_id: str, lead_id: str, reason: str) -> Dict[str, Any]:
        """V2.2: Stop all future messages for a lead in this campaign.
        
        Args:
            campaign_id: Campaign UUID
            lead_id: Lead UUID
            reason: 'unsubscribe', 'bounce', or 'manual'
            
        Returns:
            Dict with ok, canceled_count, reason
        """
        # Update lead flags (done in leads_store separately)
        # Here we just cancel messages
        
        now = datetime.utcnow()
        canceled_count = 0
        
        for message in self.messages.values():
            if (message.campaign_id == campaign_id and
                message.lead_id == lead_id and
                message.status == MessageStatus.queued and
                message.scheduled_at > now):
                
                message.status = MessageStatus.canceled
                message.cancel_reason = f"stopped_{reason}"
                canceled_count += 1
        
        # V2.2: Update campaign statistics (for reason tracking)
        # Note: In production, this would be a proper campaign_stats table
        # For MVP, we calculate stats on-the-fly in get_kpis()
        
        logger.info(f"Stopped lead {lead_id} in campaign {campaign_id}: {canceled_count} messages canceled (reason: {reason})")
        
        return {
            "ok": True,
            "lead_id": lead_id,
            "canceled_count": canceled_count,
            "reason": reason
        }
    
    def get_stats_breakdown(self, campaign_id: str) -> Dict[str, Any]:
        """V2.2: Get detailed stats breakdown including stop reasons.
        
        Returns:
            Dict with counts by status and cancel reasons
        """
        messages = [m for m in self.messages.values() if m.campaign_id == campaign_id]
        
        stats = {
            "total": len(messages),
            "queued": len([m for m in messages if m.status == MessageStatus.queued]),
            "sent": len([m for m in messages if m.status == MessageStatus.sent]),
            "opened": len([m for m in messages if m.status == MessageStatus.opened]),
            "failed": len([m for m in messages if m.status == MessageStatus.failed]),
            "canceled": len([m for m in messages if m.status == MessageStatus.canceled]),
            "bounced": len([m for m in messages if m.status == MessageStatus.bounced]),
            "cancel_reasons": {}
        }
        
        # Breakdown of cancel reasons
        canceled_messages = [m for m in messages if m.status == MessageStatus.canceled]
        for msg in canceled_messages:
            reason = getattr(msg, 'cancel_reason', 'unknown') or 'unknown'
            stats["cancel_reasons"][reason] = stats["cancel_reasons"].get(reason, 0) + 1
        
        return stats
    
    def get_schedule(
        self,
        campaign_id: str,
        limit: int = 200,
        domain: Optional[str] = None,
        from_ts: Optional[datetime] = None
    ) -> List[Message]:
        """V2.2: Get scheduled messages for timeline view.
        
        Returns messages ordered by:
        1. scheduled_at ASC
        2. domain_used ASC
        3. Priority (M4 > M3 > M2 > M1)
        4. lead_id ASC
        """
        # Filter messages for this campaign
        campaign_messages = [
            m for m in self.messages.values()
            if m.campaign_id == campaign_id
        ]
        
        # Apply filters
        if domain:
            campaign_messages = [m for m in campaign_messages if m.domain_used == domain]
        
        if from_ts:
            campaign_messages = [m for m in campaign_messages if m.scheduled_at >= from_ts]
        else:
            # Default: from 1 day ago
            from_ts = datetime.utcnow() - timedelta(days=1)
            campaign_messages = [m for m in campaign_messages if m.scheduled_at >= from_ts]
        
        # Sort by priority
        mail_priority = {4: 0, 3: 1, 2: 2, 1: 3}
        
        campaign_messages.sort(key=lambda m: (
            m.scheduled_at,
            m.domain_used,
            mail_priority.get(m.mail_number, 99),
            m.lead_id
        ))
        
        # Limit results
        return campaign_messages[:limit]


# Global store instance
campaign_store = CampaignStore()
