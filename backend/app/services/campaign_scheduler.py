import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from zoneinfo import ZoneInfo
from loguru import logger

from app.core.sending_policy import SENDING_POLICY
from app.core.campaign_flows import get_flow_for_domain, calculate_mail_schedule, get_followup_headers
from app.models.campaign import Campaign, Message, MessageStatus, CampaignStatus
from app.models.lead import Lead
from app.schemas.campaign import CampaignCreatePayload, DryRunDay


class CampaignScheduler:
    """
    Handles campaign scheduling using hard-coded sending policy and flows.
    - 27 slots per workday (08:00-16:40, every 20 minutes)
    - Grace period until 18:00
    - FIFO queueing per domain
    - Max 1 active campaign per domain
    """
    
    def __init__(self):
        # In-memory tracking for MVP (replace with Redis/DB in production)
        self.domain_queues: Dict[str, List[Dict]] = {}  # FIFO queue per domain
        self.domain_last_send: Dict[str, datetime] = {}
        self.active_campaigns: Dict[str, str] = {}  # domain -> campaign_id
    
    def schedule_campaign(self, campaign: Campaign, lead_ids: List[str]) -> Dict:
        """Schedule campaign using domain flow and sending policy."""
        
        # Get flow for campaign domain
        flow = get_flow_for_domain(campaign.domain)
        if not flow:
            raise ValueError(f"No flow configured for domain: {campaign.domain}")
        
        # Check if domain is busy
        if campaign.domain in self.active_campaigns:
            raise ValueError(f"Domain {campaign.domain} is busy with campaign {self.active_campaigns[campaign.domain]}")
        
        # Calculate start time
        start_at = campaign.start_at or datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        # Calculate mail schedule using flow
        mail_schedule = calculate_mail_schedule(start_at, flow)
        
        # Filter out stopped leads (lazy import to avoid circular imports)
        from app.services.leads_store import leads_store
        active_lead_ids = [lead_id for lead_id in lead_ids if not leads_store.is_stopped(lead_id)]
        
        if not active_lead_ids:
            logger.warning(f"All leads are stopped for campaign {campaign.id}")
            return {
                "campaign_id": campaign.id,
                "domain": campaign.domain,
                "total_messages": 0,
                "mail_schedule": {},
                "flow_version": flow.version if flow else "unknown"
            }
        
        # Create messages for each mail in flow
        messages = []
        for mail_number, scheduled_at in mail_schedule.items():
            for lead_id in active_lead_ids:
                # Get alias for this mail
                alias = flow.get_alias_for_mail(mail_number)
                headers = get_followup_headers(mail_number)
                
                message = Message(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign.id,
                    lead_id=lead_id,
                    domain_used=campaign.domain,
                    mail_number=mail_number,
                    alias=alias,
                    from_email=headers["from"],
                    reply_to_email=headers["reply_to"],
                    scheduled_at=scheduled_at,
                    status=MessageStatus.queued,
                    is_followup=(mail_number > 1),
                    retry_count=0
                )
                messages.append(message)
        
        # Add to domain queue (FIFO)
        if campaign.domain not in self.domain_queues:
            self.domain_queues[campaign.domain] = []
        
        # Add all messages to queue
        for message in messages:
            self.domain_queues[campaign.domain].append({
                "message": message,
                "scheduled_at": message.scheduled_at
            })
        
        # Mark domain as busy
        self.active_campaigns[campaign.domain] = campaign.id
        
        logger.info(f"Scheduled campaign {campaign.id} on domain {campaign.domain} with {len(messages)} messages")
        
        return {
            "campaign_id": campaign.id,
            "domain": campaign.domain,
            "total_messages": len(messages),
            "mail_schedule": mail_schedule,
            "flow_version": flow.version
        }
    
    def get_next_messages_to_send(self, domain: str, current_time: Optional[datetime] = None) -> List[Message]:
        """Get next messages to send for domain (FIFO queue)."""
        if current_time is None:
            current_time = datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        if domain not in self.domain_queues:
            return []
        
        # Check if within grace period
        if not SENDING_POLICY.is_within_grace_period(current_time):
            logger.info(f"Outside grace period, moving remaining messages to next day")
            self._move_remaining_to_next_day(domain, current_time)
            return []
        
        # Get messages ready to send (FIFO)
        ready_messages = []
        queue = self.domain_queues[domain]
        
        # Check throttle (1 email per 20 minutes per domain)
        last_send = self.domain_last_send.get(domain)
        if last_send:
            time_since_last = (current_time - last_send).total_seconds() / 60
            if time_since_last < SENDING_POLICY.slot_every_minutes:
                logger.debug(f"Domain {domain} throttled, {time_since_last:.1f}min since last send")
                return []
        
        # Get all messages in queue that are ready
        while queue:
            item = queue[0]
            message = item["message"]
            scheduled_at = item["scheduled_at"]
            
            if scheduled_at <= current_time:
                # Message is ready to send
                ready_messages.append(message)
                queue.pop(0)  # Remove from queue (FIFO)
                
                # Update last send time
                self.domain_last_send[domain] = current_time
                
                logger.info(f"Ready to send message {message.id} for domain {domain}")
            else:
                # No more ready messages
                break
        
        return ready_messages
    
    def _move_remaining_to_next_day(self, domain: str, current_time: datetime):
        """Move remaining messages to next valid day at 08:00."""
        if domain not in self.domain_queues:
            return
        
        queue = self.domain_queues[domain]
        next_day_start = SENDING_POLICY.get_next_valid_slot(current_time + timedelta(days=1))
        
        # Move all remaining messages to next day
        for item in queue:
            message = item["message"]
            if message.scheduled_at.date() == current_time.date():
                # Reschedule to next valid day
                item["scheduled_at"] = next_day_start
                message.scheduled_at = next_day_start
                
                logger.info(f"Moved message {message.id} to next day: {next_day_start}")
    
    def complete_campaign(self, campaign_id: str, domain: str):
        """Mark campaign as completed and free up domain."""
        if domain in self.active_campaigns and self.active_campaigns[domain] == campaign_id:
            del self.active_campaigns[domain]
            logger.info(f"Campaign {campaign_id} completed, domain {domain} is now available")
        
        # Clean up empty queue
        if domain in self.domain_queues and len(self.domain_queues[domain]) == 0:
            del self.domain_queues[domain]
    
    def get_domain_status(self) -> Dict[str, Dict]:
        """Get status of all domains."""
        status = {}
        
        for domain in ["punthelder-marketing.nl", "punthelder-vindbaarheid.nl", 
                      "punthelder-seo.nl", "punthelder-zoekmachine.nl"]:
            
            active_campaign = self.active_campaigns.get(domain)
            queue_size = len(self.domain_queues.get(domain, []))
            last_send = self.domain_last_send.get(domain)
            
            status[domain] = {
                "active_campaign": active_campaign,
                "queue_size": queue_size,
                "last_send": last_send.isoformat() if last_send else None,
                "is_busy": active_campaign is not None
            }
        
        return status
    
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
