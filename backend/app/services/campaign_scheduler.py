import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from zoneinfo import ZoneInfo
from loguru import logger

from app.models.campaign import Campaign, Message, MessageStatus, CampaignStatus
from app.models.lead import Lead
from app.schemas.campaign import CampaignCreatePayload, DryRunDay


class CampaignScheduler:
    """
    Handles campaign scheduling with Europe/Amsterdam timezone,
    sending window (Mon-Fri 08:00-17:00), and throttling (1 email/20min/domain).
    """
    
    TIMEZONE = ZoneInfo("Europe/Amsterdam")
    WORK_DAYS = [0, 1, 2, 3, 4]  # Monday=0 to Friday=4
    WORK_START_HOUR = 8
    WORK_END_HOUR = 17
    THROTTLE_MINUTES = 20
    
    def __init__(self):
        self.domains_available = ["domain1.com", "domain2.com", "domain3.com", "domain4.com"]
        # In-memory tracking for MVP (replace with Redis/DB in production)
        self.domain_last_send: Dict[str, datetime] = {}
    
    def create_campaign_messages(
        self, 
        campaign: Campaign, 
        lead_ids: List[str], 
        domains: List[str],
        start_at: Optional[datetime] = None
    ) -> List[Message]:
        """Create scheduled messages for a campaign."""
        
        if start_at is None:
            start_at = datetime.now(self.TIMEZONE)
        
        # Get next valid sending slot
        next_slot = self._get_next_valid_slot(start_at)
        
        messages = []
        domain_slots: Dict[str, datetime] = {domain: next_slot for domain in domains}
        
        for lead_id in lead_ids:
            # Round-robin domain assignment
            domain = self._get_next_available_domain(domains, domain_slots)
            
            # Create message
            message = Message(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                lead_id=lead_id,
                domain_used=domain,
                scheduled_at=domain_slots[domain],
                status=MessageStatus.queued
            )
            messages.append(message)
            
            # Advance slot for this domain
            domain_slots[domain] = self._get_next_slot_for_domain(domain_slots[domain])
            
            logger.info(f"Scheduled message {message.id} for lead {lead_id} at {message.scheduled_at}")
        
        return messages
    
    def dry_run_planning(
        self, 
        lead_count: int, 
        domains: List[str],
        start_at: Optional[datetime] = None
    ) -> List[DryRunDay]:
        """Simulate campaign planning without creating actual messages."""
        
        if start_at is None:
            start_at = datetime.now(self.TIMEZONE)
        
        next_slot = self._get_next_valid_slot(start_at)
        domain_slots: Dict[str, datetime] = {domain: next_slot for domain in domains}
        
        # Track messages per day
        daily_counts: Dict[str, int] = {}
        
        for i in range(lead_count):
            domain = domains[i % len(domains)]  # Simple round-robin for dry run
            slot_time = domain_slots[domain]
            
            # Count by date
            date_key = slot_time.strftime("%Y-%m-%d")
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            
            # Advance slot
            domain_slots[domain] = self._get_next_slot_for_domain(slot_time)
        
        # Convert to response format
        return [
            DryRunDay(date=date, planned=count)
            for date, count in sorted(daily_counts.items())
        ]
    
    def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a running campaign (messages remain scheduled)."""
        # In production: update campaign status in DB
        logger.info(f"Pausing campaign {campaign_id}")
        return True
    
    def resume_campaign(self, campaign_id: str) -> bool:
        """Resume a paused campaign (reschedule pending messages)."""
        # In production: reschedule queued messages to valid slots
        logger.info(f"Resuming campaign {campaign_id}")
        return True
    
    def stop_campaign(self, campaign_id: str) -> bool:
        """Stop a campaign (cancel all queued messages)."""
        # In production: set queued messages to canceled status
        logger.info(f"Stopping campaign {campaign_id}")
        return True
    
    def schedule_followup(
        self, 
        original_message: Message, 
        followup_days: int,
        attach_report: bool = False
    ) -> Message:
        """Schedule a follow-up message X days after original was sent."""
        
        if not original_message.sent_at:
            raise ValueError("Cannot schedule follow-up for unsent message")
        
        # Calculate follow-up date
        followup_date = original_message.sent_at + timedelta(days=followup_days)
        followup_slot = self._get_next_valid_slot(followup_date)
        
        followup_message = Message(
            id=str(uuid.uuid4()),
            campaign_id=original_message.campaign_id,
            lead_id=original_message.lead_id,
            domain_used=original_message.domain_used,
            scheduled_at=followup_slot,
            status=MessageStatus.queued,
            parent_message_id=original_message.id,
            is_followup=True
        )
        
        logger.info(f"Scheduled follow-up {followup_message.id} for {followup_slot}")
        return followup_message
    
    def _get_next_valid_slot(self, from_time: datetime) -> datetime:
        """Get next valid sending slot respecting work hours and days."""
        
        # Ensure timezone
        if from_time.tzinfo is None:
            from_time = from_time.replace(tzinfo=self.TIMEZONE)
        else:
            from_time = from_time.astimezone(self.TIMEZONE)
        
        current = from_time
        
        while True:
            # Check if current time is within work hours and days
            if (current.weekday() in self.WORK_DAYS and 
                self.WORK_START_HOUR <= current.hour < self.WORK_END_HOUR):
                return current
            
            # Move to next work period
            if current.weekday() not in self.WORK_DAYS:
                # Weekend - move to Monday 08:00
                days_until_monday = (7 - current.weekday()) % 7
                if days_until_monday == 0:  # Already Monday
                    days_until_monday = 7
                current = current.replace(
                    hour=self.WORK_START_HOUR, 
                    minute=0, 
                    second=0, 
                    microsecond=0
                ) + timedelta(days=days_until_monday)
            elif current.hour < self.WORK_START_HOUR:
                # Before work hours - move to 08:00 same day
                current = current.replace(
                    hour=self.WORK_START_HOUR, 
                    minute=0, 
                    second=0, 
                    microsecond=0
                )
            else:
                # After work hours - move to next work day 08:00
                current = current.replace(
                    hour=self.WORK_START_HOUR, 
                    minute=0, 
                    second=0, 
                    microsecond=0
                ) + timedelta(days=1)
    
    def _get_next_available_domain(
        self, 
        domains: List[str], 
        domain_slots: Dict[str, datetime]
    ) -> str:
        """Get domain with earliest available slot."""
        return min(domains, key=lambda d: domain_slots[d])
    
    def _get_next_slot_for_domain(self, current_slot: datetime) -> datetime:
        """Get next available slot for a domain (respecting throttle)."""
        next_slot = current_slot + timedelta(minutes=self.THROTTLE_MINUTES)
        return self._get_next_valid_slot(next_slot)
    
    def _is_work_time(self, dt: datetime) -> bool:
        """Check if datetime is within work hours and days."""
        return (dt.weekday() in self.WORK_DAYS and 
                self.WORK_START_HOUR <= dt.hour < self.WORK_END_HOUR)
