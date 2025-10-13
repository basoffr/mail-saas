import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from zoneinfo import ZoneInfo
from loguru import logger

from app.core.sending_policy import SENDING_POLICY
from app.core.campaign_flows import get_flow_for_domain, calculate_mail_schedule, get_followup_headers
from app.core.stream_calculator import get_stream_for_mail, snap_to_stream_slot
from app.models.campaign import Campaign, Message, MessageStatus, CampaignStatus
from app.models.lead import Lead
from app.schemas.campaign import CampaignCreatePayload, DryRunDay


# V2.2: Multi-domain parallel scheduling with dual-lane (alias-based)
DOMAINS = [
    "punthelder-vindbaarheid.nl",
    "punthelder-seo.nl",
    "punthelder-zoekmachine.nl",
    "punthelder-marketing.nl"
]


def assign_lead_domains(lead_ids: List[str]) -> Dict[str, str]:
    """Assign domain to each lead using modulo 4 pattern.
    
    Args:
        lead_ids: List of lead UUIDs (ordered)
        
    Returns:
        Dict mapping lead_id → domain
        
    Example:
        ['uuid1', 'uuid2', 'uuid3', 'uuid4', 'uuid5']
        → {'uuid1': 'vindbaarheid', 'uuid2': 'seo', ...}
    """
    assignments = {}
    for idx, lead_id in enumerate(lead_ids):
        domain = DOMAINS[idx % 4]
        assignments[lead_id] = domain
    
    logger.debug(f"Assigned {len(lead_ids)} leads across {len(DOMAINS)} domains")
    return assignments


class CampaignScheduler:
    """
    Handles campaign scheduling using hard-coded sending policy and flows.
    - 54 slots per workday (27 Stream A + 27 Stream B)
    - Dual-lane per domain (christian@ + victor@)
    - Lead-level domain assignment (modulo 4)
    - Grace period until 18:00
    """
    
    # Class constants for backwards compatibility with old methods
    TIMEZONE = ZoneInfo("Europe/Amsterdam")
    WORK_DAYS = [0, 1, 2, 3, 4]  # Monday-Friday (weekday numbers)
    WORK_START_HOUR = 8
    WORK_END_HOUR = 17
    THROTTLE_MINUTES = 20
    
    def __init__(self):
        # In-memory tracking for MVP (replace with Redis/DB in production)
        self.domain_queues: Dict[str, List[Dict]] = {}  # FIFO queue per domain
        self.domain_last_send: Dict[str, datetime] = {}
        self.active_campaigns: Dict[str, str] = {}  # domain -> campaign_id
    
    def schedule_campaign(self, campaign: Campaign, lead_ids: List[str]) -> Dict:
        """Schedule campaign using lead-level domain assignment and stream-based slots."""
        
        # Calculate start time
        start_at = campaign.start_at or datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        # Filter out stopped leads (use factory to get correct store)
        from app.services.store_factory import leads_store
        active_lead_ids = [lead_id for lead_id in lead_ids if not leads_store.is_stopped(lead_id)]
        
        if not active_lead_ids:
            logger.warning(f"All leads are stopped for campaign {campaign.id}")
            return {
                "campaign_id": campaign.id,
                "domains_used": [],
                "total_messages": 0,
                "leads_per_domain": {}
            }
        
        # V2.2: Assign domain to each lead (modulo 4 pattern)
        lead_domain_map = assign_lead_domains(active_lead_ids)
        
        # Create messages for each lead
        messages = []
        domain_distribution = {d: 0 for d in DOMAINS}
        
        for lead_id in active_lead_ids:
            # Get assigned domain for this lead
            lead_domain = lead_domain_map[lead_id]
            domain_distribution[lead_domain] += 1
            
            # Get flow for this domain
            flow = get_flow_for_domain(lead_domain)
            if not flow:
                logger.error(f"No flow for domain {lead_domain}")
                continue
            
            # Schedule each mail for this lead
            for step in flow.steps:
                mail_number = step.mail_number
                
                # Calculate target date (workdays offset from start)
                target_date = start_at
                workdays_added = 0
                
                while workdays_added < step.workdays_offset:
                    target_date += timedelta(days=1)
                    if SENDING_POLICY.is_valid_sending_day(target_date):
                        workdays_added += 1
                
                # V2.2: Determine stream for this mail
                stream = get_stream_for_mail(mail_number)
                
                # Snap to valid slot in correct stream
                scheduled_at = snap_to_stream_slot(target_date, stream)
                
                # Ensure it's during work hours
                scheduled_at = SENDING_POLICY.get_next_valid_slot(scheduled_at)
                
                # Get alias and headers
                alias = flow.get_alias_for_mail(mail_number)
                from_email = f"{alias}@{lead_domain}"
                reply_to_email = f"christian@{lead_domain}"
                
                # Create message
                message = Message(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign.id,
                    lead_id=lead_id,
                    domain_used=lead_domain,  # LEAD-SPECIFIC!
                    mail_number=mail_number,
                    alias=alias,
                    from_email=from_email,
                    reply_to_email=reply_to_email,
                    scheduled_at=scheduled_at,
                    status=MessageStatus.queued,
                    is_followup=(mail_number > 1),
                    retry_count=0
                )
                messages.append(message)
        
        # Add to domain queues (per domain)
        for message in messages:
            domain = message.domain_used
            if domain not in self.domain_queues:
                self.domain_queues[domain] = []
            
            self.domain_queues[domain].append({
                "message": message,
                "scheduled_at": message.scheduled_at
            })
        
        # Mark all domains as active
        for domain in DOMAINS:
            if domain_distribution[domain] > 0:
                self.active_campaigns[domain] = campaign.id
        
        logger.info(
            f"Scheduled campaign {campaign.id}: {len(messages)} messages "
            f"across {len([d for d in domain_distribution.values() if d > 0])} domains"
        )
        
        return {
            "campaign_id": campaign.id,
            "domains_used": DOMAINS,
            "total_messages": len(messages),
            "leads_per_domain": domain_distribution
        }
    
    def create_campaign_messages(
        self,
        campaign: Campaign,
        lead_ids: List[str],
        domains: List[str],
        start_at: Optional[datetime] = None
    ) -> List[Message]:
        """V2.2: Create and schedule messages for a campaign.
        
        Args:
            campaign: Campaign object
            lead_ids: List of lead UUIDs to schedule
            domains: List of domains (not used - kept for backwards compat)
            start_at: Optional start datetime. If None, uses next available slot.
        
        Returns:
            List of Message objects ready to be stored
        """
        # Update campaign with start_at if provided
        if start_at:
            campaign.start_at = start_at
        
        # Calculate effective start time
        effective_start = start_at or datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        # Filter out stopped leads (use factory to get correct store)
        from app.services.store_factory import leads_store
        active_lead_ids = [lead_id for lead_id in lead_ids if not leads_store.is_stopped(lead_id)]
        
        if not active_lead_ids:
            logger.warning(f"All leads are stopped for campaign {campaign.id}")
            return []
        
        # V2.2: Assign domain to each lead (modulo 4 pattern)
        lead_domain_map = assign_lead_domains(active_lead_ids)
        
        # Create messages for each lead
        messages = []
        
        for lead_id in active_lead_ids:
            # Get assigned domain for this lead
            lead_domain = lead_domain_map[lead_id]
            
            # Get flow for this domain
            flow = get_flow_for_domain(lead_domain)
            if not flow:
                logger.error(f"No flow for domain {lead_domain}")
                continue
            
            # Schedule each mail (M1-M4) for this lead
            for step in flow.steps:
                mail_number = step.mail_number
                
                # Calculate target date (workdays offset from start)
                target_date = effective_start
                workdays_added = 0
                
                while workdays_added < step.workdays_offset:
                    target_date += timedelta(days=1)
                    if SENDING_POLICY.is_valid_sending_day(target_date):
                        workdays_added += 1
                
                # V2.2: Determine stream for this mail
                stream = get_stream_for_mail(mail_number)
                
                # Snap to valid slot in correct stream
                scheduled_at = snap_to_stream_slot(target_date, stream)
                
                # Ensure it's during work hours
                scheduled_at = SENDING_POLICY.get_next_valid_slot(scheduled_at)
                
                # Get alias and headers
                alias = flow.get_alias_for_mail(mail_number)
                from_email = f"{alias}@{lead_domain}"
                reply_to_email = f"christian@{lead_domain}"
                
                # Create message
                message = Message(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign.id,
                    lead_id=lead_id,
                    domain_used=lead_domain,
                    mail_number=mail_number,
                    alias=alias,
                    from_email=from_email,
                    reply_to_email=reply_to_email,
                    scheduled_at=scheduled_at,
                    status=MessageStatus.queued,
                    is_followup=(mail_number > 1),
                    retry_count=0
                )
                messages.append(message)
        
        logger.info(
            f"Created {len(messages)} messages for campaign {campaign.id} "
            f"({len(active_lead_ids)} leads, start: {effective_start.strftime('%Y-%m-%d %H:%M')})"
        )
        
        return messages
    
    def get_next_messages_to_send(self, domain: str, current_time: Optional[datetime] = None) -> List[Message]:
        """V2.2: Get next messages using dual-lane (alias-based) priority selection.
        
        Returns up to 2 messages per slot:
        - Lane A: 1 message from christian@ (highest priority)
        - Lane B: 1 message from victor@ (highest priority)
        """
        if current_time is None:
            current_time = datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        if domain not in self.domain_queues:
            return []
        
        # Check if within grace period
        if not SENDING_POLICY.is_within_grace_period(current_time):
            logger.info(f"Outside grace period, moving remaining messages to next day")
            self._move_remaining_to_next_day(domain, current_time)
            return []
        
        # Round to current slot (:00, :10, :20, :30, :40, :50)
        current_slot = self._round_to_slot(current_time)
        
        # Get ALL messages for this domain at this EXACT slot time
        queue = self.domain_queues[domain]
        due_messages = [
            item["message"] for item in queue
            if item["scheduled_at"] == current_slot
        ]
        
        if not due_messages:
            logger.debug(f"No messages due for {domain} at slot {current_slot}")
            return []
        
        # V2.2: Split by alias (dual-lane)
        christian_msgs = [m for m in due_messages if m.alias == "christian"]
        victor_msgs = [m for m in due_messages if m.alias == "victor"]
        
        # Sort each lane by priority (M4 > M3 > M2 > M1)
        mail_priority = {4: 0, 3: 1, 2: 2, 1: 3}
        
        christian_msgs.sort(key=lambda m: (mail_priority.get(m.mail_number, 99), m.lead_id))
        victor_msgs.sort(key=lambda m: (mail_priority.get(m.mail_number, 99), m.lead_id))
        
        # Select top message from each lane
        selected = []
        
        # Lane A: christian@
        if christian_msgs:
            lane_a = christian_msgs[0]
            selected.append(lane_a)
            logger.info(f"Lane A (christian): {domain} M{lane_a.mail_number} lead {lane_a.lead_id}")
        
        # Lane B: victor@
        if victor_msgs:
            lane_b = victor_msgs[0]
            selected.append(lane_b)
            logger.info(f"Lane B (victor): {domain} M{lane_b.mail_number} lead {lane_b.lead_id}")
        
        # Remove selected messages from queue
        for message in selected:
            for item in queue[:]:
                if item["message"].id == message.id:
                    queue.remove(item)
                    break
        
        # Update last send time
        if selected:
            self.domain_last_send[domain] = current_time
        
        logger.info(f"Selected {len(selected)} messages for {domain} at slot {current_slot}")
        return selected
    
    def _round_to_slot(self, dt: datetime) -> datetime:
        """Round datetime to nearest 10-minute slot.
        
        Slots: :00, :10, :20, :30, :40, :50
        """
        minute = dt.minute
        slot_minute = (minute // 10) * 10
        return dt.replace(minute=slot_minute, second=0, microsecond=0)
    
    def cancel_future_messages(self, lead_id: str, after_mail_number: int) -> int:
        """V2.2: Cancel all future messages for a lead (stop criteria).
        
        Called when a lead:
        - Replies to any email
        - Unsubscribes
        - Bounces
        
        Args:
            lead_id: Lead UUID
            after_mail_number: Cancel messages with mail_number > this
            
        Returns:
            Number of messages canceled
            
        Example:
            cancel_future_messages(lead_id, 1)
            → Cancels M2, M3, M4 for this lead
        """
        canceled_count = 0
        
        # Iterate through all domain queues
        for domain in DOMAINS:
            if domain not in self.domain_queues:
                continue
            
            queue = self.domain_queues[domain]
            
            # Find and cancel matching messages
            for item in queue[:]:
                message = item["message"]
                
                if (message.lead_id == lead_id and 
                    message.mail_number > after_mail_number and
                    message.status == MessageStatus.queued):
                    
                    # Cancel the message
                    message.status = MessageStatus.canceled
                    queue.remove(item)
                    canceled_count += 1
                    
                    logger.info(
                        f"Canceled M{message.mail_number} for lead {lead_id} "
                        f"(stop criteria after M{after_mail_number})"
                    )
        
        return canceled_count
    
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
        """Simulate campaign planning using flow-based scheduling.
        
        Uses the same logic as actual campaign scheduling:
        - Each lead gets 4 mails (flow steps)
        - Mails scheduled based on domain flow (christian/victor, workday offsets)
        - 20-minute throttling between mails on same domain
        """
        
        if start_at is None:
            start_at = datetime.now(self.TIMEZONE)
        
        # Track messages per day
        daily_counts: Dict[str, int] = {}
        
        # Get flow for first domain (all have same structure)
        from app.core.campaign_flows import get_flow_for_domain, calculate_mail_schedule
        
        if not domains:
            return []
        
        domain = domains[0]  # Use first domain for flow structure
        flow = get_flow_for_domain(domain)
        
        if not flow:
            # Fallback to old logic if no flow found
            logger.warning(f"No flow found for domain {domain}, using fallback")
            return self._dry_run_fallback(lead_count, domains, start_at)
        
        # For each lead, schedule all mails in the flow
        for lead_idx in range(lead_count):
            # Calculate base schedule for this lead
            mail_schedule = calculate_mail_schedule(start_at, flow)
            
            # Add each mail to daily counts
            for mail_number, scheduled_at in mail_schedule.items():
                date_key = scheduled_at.strftime("%Y-%m-%d")
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        # Convert to response format
        return [
            DryRunDay(date=date, planned=count)
            for date, count in sorted(daily_counts.items())
        ]
    
    def _dry_run_fallback(
        self,
        lead_count: int,
        domains: List[str],
        start_at: datetime
    ) -> List[DryRunDay]:
        """Fallback dry-run logic when no flow is available."""
        next_slot = self._get_next_valid_slot(start_at)
        domain_slots: Dict[str, datetime] = {domain: next_slot for domain in domains}
        
        daily_counts: Dict[str, int] = {}
        
        for i in range(lead_count):
            domain = domains[i % len(domains)]
            slot_time = domain_slots[domain]
            
            date_key = slot_time.strftime("%Y-%m-%d")
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            
            domain_slots[domain] = self._get_next_slot_for_domain(slot_time)
        
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
