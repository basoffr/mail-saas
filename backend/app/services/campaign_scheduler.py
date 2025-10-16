import uuid
from datetime import datetime, timedelta, date, time
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
        # PRODUCTION-READY: Database-driven architecture
        # Messages are stored in Supabase, not in-memory
        
        # DEPRECATED: domain_queues no longer used (kept for backward compat with tests)
        self.domain_queues: Dict[str, List[Dict]] = {}  # DEPRECATED - use database queries
        
        # In-memory optimizations (not critical, survives restart gracefully)
        self.domain_last_send: Dict[str, datetime] = {}  # For throttling optimization
        self.active_campaigns: Dict[str, str] = {}  # domain → campaign_id mapping
        self.domain_active_dates: Dict[str, date] = {}  # domain → active date tracking
    
    def _validate_slot_day_and_hour(self, dt: datetime, stream: str) -> datetime:
        """Validate day and hour are valid, preserve stream minutes AND timezone.
        
        This is stream-aware alternative to get_next_valid_slot that preserves
        the stream's minute alignment (:00/:20/:40 for A, :10/:30/:50 for B)
        AND preserves timezone info (critical for Europe/Amsterdam DST handling).
        
        IMPORTANT: datetime.replace(tzinfo=...) does NOT work correctly for DST-aware zones!
        We must use proper timezone conversion to maintain correct UTC offset.
        """
        from app.core.stream_calculator import get_stream_slot_minutes
        
        # Get valid minutes for this stream
        stream_minutes = get_stream_slot_minutes(stream)
        
        # If weekend, move to next Monday and reset to first stream slot
        while not SENDING_POLICY.is_valid_sending_day(dt):
            dt += timedelta(days=1)
        
        # If we skipped to a new day, reset to window start
        window_start_hour, _ = map(int, SENDING_POLICY.window_from.split(':'))
        window_end_hour, window_end_min = map(int, SENDING_POLICY.window_to.split(':'))
        
        # If before window, set to window start with first stream slot
        if dt.time() < time(window_start_hour, 0):
            # Create new datetime with same date but new time, preserving timezone
            dt = dt.replace(hour=window_start_hour, minute=stream_minutes[0], second=0, microsecond=0)
        
        # If after window, move to next day with first stream slot  
        elif dt.time() >= time(window_end_hour, window_end_min):
            dt += timedelta(days=1)
            dt = dt.replace(hour=window_start_hour, minute=stream_minutes[0], second=0, microsecond=0)
            # Check if new day is valid
            while not SENDING_POLICY.is_valid_sending_day(dt):
                dt += timedelta(days=1)
                dt = dt.replace(hour=window_start_hour, minute=stream_minutes[0], second=0, microsecond=0)
        
        return dt
    
    def _find_next_available_slot(
        self,
        domain: str,
        target_date: datetime,
        stream: str,
        alias: str,
        slot_tracker: Dict[Tuple[str, datetime, str], int]
    ) -> datetime:
        """V2.3: Find next available slot for a message with capacity tracking (STREAM-AWARE).
        
        Spreads messages across available slots based on:
        - Domain
        - Stream (A: M1/M3 at :00/:20/:40, B: M2/M4 at :10/:30/:50)
        - Alias (christian or victor for dual-lane)
        - Max 1 message per (domain, slot, alias) combination
        
        Args:
            domain: The sending domain
            target_date: Target date for this mail (after workday offset)
            stream: Stream identifier ('A' or 'B')
            alias: Sender alias ('christian' or 'victor')
            slot_tracker: Dictionary tracking slot usage
        
        Returns:
            Next available scheduled_at datetime
        """
        # Start with initial slot in correct stream
        current_slot = snap_to_stream_slot(target_date, stream)
        current_slot = self._validate_slot_day_and_hour(current_slot, stream)
        
        # Max iterations to prevent infinite loop
        # For 2103 leads * 4 messages = 8412 messages, we need much more headroom
        # 100 workdays * 27 slots/day = 2700 slots should be more than enough
        max_iterations = 100 * 27  # 2700 slot checks
        iteration = 0
        
        # Track initial slot for debugging
        initial_slot = current_slot
        
        while iteration < max_iterations:
            # Check if this slot is available for this domain/alias combination
            slot_key = (domain, current_slot, alias)
            current_count = slot_tracker.get(slot_key, 0)
            
            # Max 1 message per (domain, slot, alias) for dual-lane
            if current_count < 1:
                # Slot is available! Reserve it and return
                slot_tracker[slot_key] = current_count + 1
                
                # Log if we had to search far from initial slot (debugging)
                if iteration > 100:
                    logger.warning(
                        f"Took {iteration} iterations to find slot for {domain}/{alias} "
                        f"(initial: {initial_slot.date()}, found: {current_slot.date()})"
                    )
                
                return current_slot
            
            # Slot full, move to next slot in stream
            # Stream A: :00, :20, :40 (20 min intervals)
            # Stream B: :10, :30, :50 (20 min intervals)
            current_slot += timedelta(minutes=20)
            
            # Ensure still valid (within work hours, workdays) - STREAM AWARE!
            current_slot = self._validate_slot_day_and_hour(current_slot, stream)
            
            iteration += 1
        
        # Fallback: return original slot if we hit max iterations (should NEVER happen!)
        logger.error(
            f"CRITICAL: Hit max iterations ({max_iterations}) finding slot for {domain}/{alias}! "
            f"Initial slot: {initial_slot}, current slot: {current_slot}. "
            f"This indicates a bug in slot tracking logic!"
        )
        return snap_to_stream_slot(target_date, stream)
    
    def schedule_campaign(self, campaign: Campaign, lead_ids: List[str]) -> Dict:
        """Schedule campaign using lead-level domain assignment and stream-based slots."""
        
        # Calculate start time
        start_at = campaign.start_at or datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        # V2.2: PERFORMANCE - Batch check stopped leads (1 query vs 2100 queries!)
        from app.services.store_factory import leads_store
        
        # Use batch_is_stopped for performance with large campaigns
        if hasattr(leads_store, 'batch_is_stopped'):
            stopped_map = leads_store.batch_is_stopped(lead_ids)
            active_lead_ids = [lead_id for lead_id, is_stopped in stopped_map.items() if not is_stopped]
            logger.info(f"Batch filtered {len(lead_ids)} leads -> {len(active_lead_ids)} active")
        else:
            # Fallback to individual checks (in-memory store)
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
        message_counter = 0  # ABSOLUTE counter for debugging first message
        
        logger.warning(f"🚀 STARTING MESSAGE CREATION for {len(active_lead_ids)} leads")
        
        for idx, lead_id in enumerate(active_lead_ids):
            # Get assigned domain for this lead
            lead_domain = lead_domain_map[lead_id]
            domain_distribution[lead_domain] += 1
            
            # Get flow for this domain
            flow = get_flow_for_domain(lead_domain)
            if not flow:
                logger.error(f"No flow for domain {lead_domain}")
                continue
            
            # DEBUG: Log flow for first 5 leads to verify version is correct
            if idx < 5:
                logger.warning(
                    f"[DEBUG-LEAD-{idx+1}] domain={lead_domain}, "
                    f"flow.version={flow.version}, flow.domain={flow.domain}"
                )
            
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
                
                # V2.2: Calculate template_id (e.g., v2m3 = version 2, mail 3)
                template_version = flow.version
                calculated_template_id = f"v{template_version}m{mail_number}"
                
                # NUCLEAR DEBUG: PRINT to stdout (can't be filtered!)
                if message_counter == 0:  # ABSOLUTE first message!
                    print(f"\n{'='*80}")
                    print(f"🔥🔥🔥 FIRST MESSAGE BEFORE CREATION")
                    print(f"message_counter={message_counter}, idx={idx}, mail_number={mail_number}")
                    print(f"template_version={template_version} (type={type(template_version)})")
                    print(f"calculated_template_id={calculated_template_id!r} (type={type(calculated_template_id)})")
                    print(f"flow.version={flow.version}")
                    print(f"flow.steps order={[s.mail_number for s in flow.steps]}")
                    print(f"{'='*80}\n")
                    import sys
                    sys.stdout.flush()  # Force flush to ensure it appears
                
                # CRITICAL: Assert these are NOT None before passing to Message()
                assert template_version is not None, f"template_version is None! flow.version={flow.version}"
                assert calculated_template_id is not None, f"calculated_template_id is None!"
                assert isinstance(template_version, int), f"template_version is not int: {type(template_version)}"
                assert isinstance(calculated_template_id, str), f"calculated_template_id is not str: {type(calculated_template_id)}"
                
                # Create message WITHOUT template fields first (SQLModel bug workaround)
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
                
                # WORKAROUND: Store in custom attributes that SQLModel CAN'T touch
                message._custom_template_version = template_version
                message._custom_template_id = calculated_template_id
                
                # Also try setting normal attributes (in case workaround doesn't work)
                message.template_version = template_version
                message.template_id = calculated_template_id
                
                # NUCLEAR DEBUG: PRINT after setting attributes
                if message_counter == 0:  # ABSOLUTE first message!
                    print(f"\n{'='*80}")
                    print(f"🔥🔥🔥 FIRST MESSAGE AFTER SETTING ATTRS")
                    print(f"message._custom_template_id={getattr(message, '_custom_template_id', 'NOT_FOUND')}")
                    print(f"message._custom_template_version={getattr(message, '_custom_template_version', 'NOT_FOUND')}")
                    print(f"message.template_id={message.template_id!r}")
                    print(f"message.template_version={message.template_version!r}")
                    print(f"message.__dict__={message.__dict__}")
                    print(f"{'='*80}\n")
                    import sys
                    sys.stdout.flush()
                
                messages.append(message)
                message_counter += 1  # Increment after appending
        
        # DATABASE-DRIVEN: Messages saved to database (tests should save manually)
        # No in-memory queue needed - worker queries database directly
        
        # Mark all domains as active (in-memory optimization, not critical)
        for domain in DOMAINS:
            if domain_distribution[domain] > 0:
                self.active_campaigns[domain] = campaign.id
        
        logger.info(
            f"✅ Created {len(messages)} messages for campaign {campaign.id} "
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
        
        # Calculate effective start time with proper timezone handling
        if start_at:
            # CRITICAL: If start_at is provided (e.g., from frontend), ensure it's in local timezone
            # Frontend sends ISO string which Pydantic parses as UTC-aware datetime
            # We need to convert this to Europe/Amsterdam timezone
            amsterdam_tz = ZoneInfo(SENDING_POLICY.timezone)
            effective_start = start_at.astimezone(amsterdam_tz)
        else:
            # No start_at provided, use current time in Amsterdam timezone
            effective_start = datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        # V2.2: PERFORMANCE - Batch check stopped leads (1 query vs N queries!)
        from app.services.store_factory import leads_store
        
        # Use batch_is_stopped for performance with large campaigns
        if hasattr(leads_store, 'batch_is_stopped'):
            stopped_map = leads_store.batch_is_stopped(lead_ids)
            active_lead_ids = [lead_id for lead_id, is_stopped in stopped_map.items() if not is_stopped]
            logger.info(f"Batch filtered {len(lead_ids)} leads -> {len(active_lead_ids)} active (create_messages)")
        else:
            # Fallback to individual checks (in-memory store)
            active_lead_ids = [lead_id for lead_id in lead_ids if not leads_store.is_stopped(lead_id)]
        
        if not active_lead_ids:
            logger.warning(f"All leads are stopped for campaign {campaign.id}")
            return {
                "scheduled_count": 0,
                "start_time": effective_start,
                "total_messages": 0,
                "leads_per_domain": {}
            }
        
        # V2.2: Assign domain to each lead (modulo 4 pattern)
        lead_domain_map = assign_lead_domains(active_lead_ids)
        
        # Create messages for each lead
        messages = []
        domain_distribution = {d: 0 for d in DOMAINS}
        message_counter = 0  # ABSOLUTE counter for debugging first message
        
        # V2.2: Slot availability tracker for proper spreading
        # Key: (domain, scheduled_at, alias) -> count of messages
        # Max 1 message per (domain, slot, alias) for dual-lane
        slot_tracker: Dict[Tuple[str, datetime, str], int] = {}
        
        logger.warning(f"🚀 STARTING MESSAGE CREATION for {len(active_lead_ids)} leads")
        
        # Count domain distribution
        for lead_id in active_lead_ids:
            lead_domain = lead_domain_map[lead_id]
            domain_distribution[lead_domain] += 1
        
        # V2.3: Keep lead-by-lead iteration (messages must be scheduled relative to each lead)
        # The slot allocation will naturally spread M1 and M2 across days
        for idx, lead_id in enumerate(active_lead_ids):
            # Get assigned domain for this lead
            lead_domain = lead_domain_map[lead_id]
            
            # Get flow for this domain
            flow = get_flow_for_domain(lead_domain)
            if not flow:
                logger.error(f"No flow for domain {lead_domain}")
                continue
            
            # Schedule each mail for this lead
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
                
                # Get alias BEFORE finding slot (needed for tracking)
                alias = flow.get_alias_for_mail(mail_number)
                
                # V2.2: Find next available slot with capacity tracking
                scheduled_at = self._find_next_available_slot(
                    domain=lead_domain,
                    target_date=target_date,
                    stream=stream,
                    alias=alias,
                    slot_tracker=slot_tracker
                )
                
                # Headers (alias already retrieved above)
                from_email = f"{alias}@{lead_domain}"
                reply_to_email = f"christian@{lead_domain}"
                
                # V2.2: Calculate template_id (e.g., v2m3 = version 2, mail 3)
                template_version = flow.version
                calculated_template_id = f"v{template_version}m{mail_number}"
                
                # NUCLEAR DEBUG: PRINT to stdout (can't be filtered!)
                if message_counter == 0:  # ABSOLUTE first message!
                    print(f"\n{'='*80}")
                    print(f"🔥🔥🔥 FIRST MESSAGE BEFORE CREATION")
                    print(f"message_counter={message_counter}, idx={idx}, mail_number={mail_number}")
                    print(f"template_version={template_version} (type={type(template_version)})")
                    print(f"calculated_template_id={calculated_template_id!r} (type={type(calculated_template_id)})")
                    print(f"flow.version={flow.version}")
                    print(f"flow.steps order={[s.mail_number for s in flow.steps]}")
                    print(f"{'='*80}\n")
                    import sys
                    sys.stdout.flush()  # Force flush to ensure it appears
                
                # CRITICAL: Assert these are NOT None before passing to Message()
                assert template_version is not None, f"template_version is None! flow.version={flow.version}"
                assert calculated_template_id is not None, f"calculated_template_id is None!"
                assert isinstance(template_version, int), f"template_version is not int: {type(template_version)}"
                assert isinstance(calculated_template_id, str), f"calculated_template_id is not str: {type(calculated_template_id)}"
                
                # Create message WITHOUT template fields first (SQLModel bug workaround)
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
                
                # WORKAROUND: Store in custom attributes that SQLModel CAN'T touch
                message._custom_template_version = template_version
                message._custom_template_id = calculated_template_id
                
                # Also try setting normal attributes (in case workaround doesn't work)
                message.template_version = template_version
                message.template_id = calculated_template_id
                
                # NUCLEAR DEBUG: PRINT after setting attributes
                if message_counter == 0:  # ABSOLUTE first message!
                    print(f"\n{'='*80}")
                    print(f"🔥🔥🔥 FIRST MESSAGE AFTER SETTING ATTRS")
                    print(f"message._custom_template_id={getattr(message, '_custom_template_id', 'NOT_FOUND')}")
                    print(f"message._custom_template_version={getattr(message, '_custom_template_version', 'NOT_FOUND')}")
                    print(f"message.template_id={message.template_id!r}")
                    print(f"message.template_version={message.template_version!r}")
                    print(f"message.__dict__={message.__dict__}")
                    print(f"{'='*80}\n")
                    import sys
                    sys.stdout.flush()
                
                messages.append(message)
                message_counter += 1  # Increment after appending
        
        # DATABASE-DRIVEN: Messages will be saved to database by calling code
        # No in-memory queue needed - worker queries database directly
        
        # Mark all domains as active (in-memory optimization, not critical)
        for domain in set(m.domain_used for m in messages):
            self.domain_active_dates[domain] = effective_start.date()
        
        logger.info(
            f"✅ Created {len(messages)} messages for campaign {campaign.id} "
            f"({len(active_lead_ids)} leads, start: {effective_start.strftime('%Y-%m-%d %H:%M')})"
        )
        
        return messages
    
    def get_next_messages_to_send(self, domain: str, current_time: Optional[datetime] = None) -> List[Message]:
        """
        Get next messages using dual-lane priority selection.
        
        PRODUCTION-READY: Database-driven (no in-memory state).
        - Restart-safe: Queries database directly
        - Horizontally scalable: No shared state
        - Consistent: Always current data
        
        Returns up to 2 messages per slot:
        - Lane A: 1 message from christian@ (highest priority)
        - Lane B: 1 message from victor@ (highest priority)
        
        Args:
            domain: Domain to process
            current_time: Current time (defaults to now)
            
        Returns:
            List of 0-2 messages ready to send
        """
        if current_time is None:
            current_time = datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        # Check if within grace period
        if not SENDING_POLICY.is_within_grace_period(current_time):
            logger.info(f"Outside grace period for {domain}")
            return []
        
        # Round to current slot (:00, :10, :20, :30, :40, :50)
        current_slot = self._round_to_slot(current_time)
        
        # DATABASE QUERY: Get queued messages for this slot
        from app.services.store_factory import campaigns_store
        due_messages = campaigns_store.get_queued_messages_for_slot(
            domain=domain,
            scheduled_at=current_slot,
            limit=100  # Safety limit
        )
        
        if not due_messages:
            logger.debug(f"No queued messages for {domain} at slot {current_slot}")
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
        
        # Update last send time (in-memory optimization, not critical)
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
        """
        Cancel all future messages for a lead (stop criteria).
        
        PRODUCTION-READY: Database-driven (no in-memory state).
        - Updates database directly
        - Restart-safe
        - Horizontally scalable
        
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
        # DATABASE OPERATION: Use store's stop_lead_flow method
        from app.services.store_factory import campaigns_store
        
        # Note: This cancels ALL future messages for the lead across all campaigns
        # We need to find the campaign_id first
        
        # Get all queued messages for this lead
        all_messages = campaigns_store.get_all_messages()
        lead_messages = [
            m for m in all_messages
            if m.lead_id == lead_id 
            and m.status == MessageStatus.queued
            and m.mail_number > after_mail_number
        ]
        
        if not lead_messages:
            logger.debug(f"No future messages to cancel for lead {lead_id}")
            return 0
        
        # Cancel each message via database
        canceled_count = 0
        for message in lead_messages:
            success = campaigns_store.update_message_status(
                message.id,
                MessageStatus.canceled,
                error=f"Lead stopped after M{after_mail_number}"
            )
            
            if success:
                canceled_count += 1
                logger.info(
                    f"Canceled M{message.mail_number} for lead {lead_id} "
                    f"(stop criteria after M{after_mail_number})"
                )
        
        return canceled_count
    
    def _move_remaining_to_next_day(self, domain: str, current_time: datetime):
        """
        DEPRECATED: No longer needed with database-driven architecture.
        
        Messages remain in database with original scheduled_at.
        Worker will automatically skip them outside grace period.
        Kept for backward compatibility with tests.
        """
        logger.debug(f"_move_remaining_to_next_day called for {domain} (no-op in DB mode)")
    
    def complete_campaign(self, campaign_id: str, domain: str):
        """Mark campaign as completed and free up domain."""
        if domain in self.active_campaigns and self.active_campaigns[domain] == campaign_id:
            del self.active_campaigns[domain]
            logger.info(f"Campaign {campaign_id} completed, domain {domain} is now available")
    
    def get_domain_status(self) -> Dict[str, Dict]:
        """
        Get status of all domains.
        
        PRODUCTION-READY: Database-driven (no in-memory state).
        - Queries database for queue sizes
        - Restart-safe
        """
        from app.services.store_factory import campaigns_store
        
        # Get queue counts from database
        queue_counts = campaigns_store.get_queued_messages_count_by_domain()
        
        status = {}
        for domain in ["punthelder-marketing.nl", "punthelder-vindbaarheid.nl", 
                      "punthelder-seo.nl", "punthelder-zoekmachine.nl"]:
            
            active_campaign = self.active_campaigns.get(domain)
            queue_size = queue_counts.get(domain, 0)
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


# Global scheduler instance
campaign_scheduler = CampaignScheduler()
