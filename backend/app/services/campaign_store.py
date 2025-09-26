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
        
        # Initialize with sample data
        self._create_sample_data()
    
    def create_campaign(self, campaign: Campaign) -> Campaign:
        """Create a new campaign."""
        self.campaigns[campaign.id] = campaign
        logger.info(f"Created campaign {campaign.id}: {campaign.name}")
        return campaign
    
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
    
    def update_campaign_status(self, campaign_id: str, status: CampaignStatus) -> bool:
        """Update campaign status."""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return False
        
        campaign.status = status
        campaign.updated_at = datetime.utcnow()
        logger.info(f"Updated campaign {campaign_id} status to {status}")
        return True
    
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
    
    def _create_sample_data(self):
        """Create sample campaigns for testing."""
        # Sample campaign 1
        campaign1 = Campaign(
            id="campaign-001",
            name="Welcome Campaign",
            template_id="welcome-001",
            start_at=datetime.utcnow() - timedelta(days=2),
            status=CampaignStatus.running,
            followup_enabled=True,
            followup_days=3,
            followup_attach_report=False
        )
        self.campaigns[campaign1.id] = campaign1
        
        # Sample campaign 2
        campaign2 = Campaign(
            id="campaign-002",
            name="Follow-up Campaign",
            template_id="followup-001",
            start_at=datetime.utcnow() + timedelta(days=1),
            status=CampaignStatus.draft,
            followup_enabled=False,
            followup_days=7,
            followup_attach_report=True
        )
        self.campaigns[campaign2.id] = campaign2
        
        # Sample messages for campaign 1
        for i in range(5):
            message = Message(
                id=f"message-{i+1:03d}",
                campaign_id=campaign1.id,
                lead_id=f"lead-{i+1:03d}",
                domain_used=f"domain{(i % 4) + 1}.com",
                scheduled_at=datetime.utcnow() - timedelta(hours=i*2),
                sent_at=datetime.utcnow() - timedelta(hours=i*2) if i < 3 else None,
                status=MessageStatus.sent if i < 2 else MessageStatus.opened if i == 2 else MessageStatus.queued
            )
            self.messages[message.id] = message


# Global store instance
campaign_store = CampaignStore()
