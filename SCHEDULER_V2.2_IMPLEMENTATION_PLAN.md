# 🚀 SCHEDULER V2.2 - IMPLEMENTATIEPLAN

**Datum**: 13 oktober 2025  
**Versie**: 2.2 (Multi-Domain Parallel Flow met Dual-Lane Throttle)  
**Status**: READY TO IMPLEMENT  

---

## 📋 **VALIDATIE COMPLEET**

✅ Excel structuur geanalyseerd (`Concept planning campagne.xlsx`)  
✅ Alle 13 user vragen beantwoord  
✅ Specifications confirmed:
- Lead-domain modulo 4 pattern
- Stream A/B tijdslots (:00/:20/:40 vs :10/:30/:50)
- Dual-lane capacity (2 mails per 20-min venster)
- Overlapping phases
- Stop criteria per fase

---

## 🎯 **IMPLEMENTATIE SCOPE**

### **Files te Wijzigen**

| File | Changes | Complexity |
|------|---------|------------|
| `campaign_flows.py` | Geen (flows blijven hetzelfde) | - |
| `sending_policy.py` | Stream A/B slot logic | Medium |
| `campaign_scheduler.py` | Lead-domain assignment, dual-lane queue | High |
| `campaigns.py` (API) | Remove domain assignment (nu lead-level) | Low |
| `db_campaign_store.py` | No schema changes | - |
| `message_sender.py` (NEW) | Worker met priority queue | High |

### **Nieuwe Componenten**

1. **Stream Calculator**: Bepaalt of mail M1/M2/M3/M4 → Stream A of B
2. **Lead-Domain Mapper**: Assigns domain per lead (modulo 4)
3. **Priority Queue**: Sorteert messages op mail_number priority
4. **Dual-Lane Selector**: Kiest Lane A (hoogste) + Lane B (M1 eerst)
5. **Stop Checker**: Annuleert M2-M4 bij reply/unsub/bounce

---

## 📐 **DETAILED IMPLEMENTATION**

### **PHASE 1: CORE LOGIC** ⭐ (Prioriteit 1)

#### **1.1 Stream Calculator**

**Nieuw bestand**: `backend/app/core/stream_calculator.py`

```python
"""Stream A/B calculator for dual-stream scheduling."""
from datetime import datetime, time

class StreamType:
    A = "A"  # M1, M3 - :00/:20/:40
    B = "B"  # M2, M4 - :10/:30/:50

def get_stream_for_mail(mail_number: int) -> str:
    """Get stream (A or B) for mail number."""
    if mail_number in [1, 3]:
        return StreamType.A
    elif mail_number in [2, 4]:
        return StreamType.B
    else:
        raise ValueError(f"Invalid mail number: {mail_number}")

def get_stream_slot_minutes() -> dict:
    """Get minute offsets for each stream."""
    return {
        StreamType.A: [0, 20, 40],      # :00, :20, :40
        StreamType.B: [10, 30, 50]      # :10, :30, :50
    }

def snap_to_stream_slot(dt: datetime, stream: str) -> datetime:
    """Snap datetime to nearest valid slot in stream."""
    stream_minutes = get_stream_slot_minutes()[stream]
    
    current_minute = dt.minute
    
    # Find next valid minute in stream
    for minute in stream_minutes:
        if current_minute <= minute:
            return dt.replace(minute=minute, second=0, microsecond=0)
    
    # No valid minute found in current hour, go to next hour
    next_hour = dt.replace(minute=stream_minutes[0], second=0, microsecond=0)
    from datetime import timedelta
    return next_hour + timedelta(hours=1)

def is_valid_stream_time(dt: datetime, stream: str) -> bool:
    """Check if datetime is on a valid stream slot."""
    stream_minutes = get_stream_slot_minutes()[stream]
    return dt.minute in stream_minutes
```

#### **1.2 Lead-Domain Assignment**

**File**: `backend/app/services/campaign_scheduler.py`

**Nieuwe functie**:
```python
from typing import Dict, List

DOMAINS = [
    "punthelder-vindbaarheid.nl",
    "punthelder-seo.nl",
    "punthelder-zoekmachine.nl",
    "punthelder-marketing.nl"
]

def assign_lead_domains(lead_ids: List[str]) -> Dict[str, str]:
    """Assign domain to each lead using modulo 4 pattern.
    
    Args:
        lead_ids: List of lead UUIDs
        
    Returns:
        Dict mapping lead_id → domain
        
    Example:
        lead_ids = ['uuid1', 'uuid2', 'uuid3', 'uuid4', 'uuid5']
        → {
            'uuid1': 'punthelder-vindbaarheid.nl',
            'uuid2': 'punthelder-seo.nl',
            'uuid3': 'punthelder-zoekmachine.nl',
            'uuid4': 'punthelder-marketing.nl',
            'uuid5': 'punthelder-vindbaarheid.nl'  # Wraps around
        }
    """
    assignments = {}
    for idx, lead_id in enumerate(lead_ids):
        domain = DOMAINS[idx % 4]
        assignments[lead_id] = domain
    
    return assignments
```

#### **1.3 Updated Message Scheduling**

**File**: `backend/app/services/campaign_scheduler.py`

**Modified `schedule_campaign()`:
```python
def schedule_campaign(
    self, 
    campaign: Campaign, 
    lead_ids: List[str]
) -> Dict:
    """Schedule campaign with lead-level domain assignment."""
    from app.core.stream_calculator import get_stream_for_mail, snap_to_stream_slot
    
    # NEW: Assign domain per lead (not campaign-level!)
    lead_domain_map = assign_lead_domains(lead_ids)
    
    # Filter stopped leads
    from app.services.leads_store import leads_store
    active_lead_ids = [
        lead_id for lead_id in lead_ids 
        if not leads_store.is_stopped(lead_id)
    ]
    
    if not active_lead_ids:
        logger.warning(f"All leads stopped for campaign {campaign.id}")
        return {
            "campaign_id": campaign.id,
            "total_messages": 0
        }
    
    # Start date (from campaign or now)
    start_at = campaign.start_at or datetime.now(ZoneInfo(SENDING_POLICY.timezone))
    
    # Create messages per lead
    messages = []
    
    for lead_id in active_lead_ids:
        # Get assigned domain for this lead
        lead_domain = lead_domain_map[lead_id]
        
        # Get flow for this domain
        flow = get_flow_for_domain(lead_domain)
        if not flow:
            logger.error(f"No flow for domain {lead_domain}")
            continue
        
        # Calculate schedule for this lead
        # Start from campaign start, calculate each mail's date
        current_date = start_at
        
        for step in flow.steps:
            mail_number = step.mail_number
            
            # Calculate target date (workdays offset from start)
            target_date = current_date
            workdays_added = 0
            
            while workdays_added < step.workdays_offset:
                target_date += timedelta(days=1)
                if SENDING_POLICY.is_valid_sending_day(target_date):
                    workdays_added += 1
            
            # Determine stream for this mail
            stream = get_stream_for_mail(mail_number)
            
            # Snap to valid slot in correct stream
            scheduled_at = snap_to_stream_slot(target_date, stream)
            
            # Ensure it's during work hours
            scheduled_at = SENDING_POLICY.get_next_valid_slot(scheduled_at)
            
            # Get alias and headers
            alias = flow.get_alias_for_mail(mail_number)
            headers = get_followup_headers(mail_number, lead_domain)
            
            # Create message
            message = Message(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                lead_id=lead_id,
                domain_used=lead_domain,  # LEAD-SPECIFIC!
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
    
    logger.info(f"Scheduled {len(messages)} messages across {len(DOMAINS)} domains")
    
    return {
        "campaign_id": campaign.id,
        "total_messages": len(messages),
        "domains_used": DOMAINS,
        "leads_per_domain": {
            d: sum(1 for lid in active_lead_ids if lead_domain_map[lid] == d)
            for d in DOMAINS
        }
    }
```

---

### **PHASE 2: DUAL-LANE PRIORITY QUEUE** ⭐ (Prioriteit 1)

#### **2.1 Priority Queue Manager**

**File**: `backend/app/services/message_queue.py` (NEW)

```python
"""Priority queue for dual-lane message scheduling."""
from typing import List, Optional, Tuple
from datetime import datetime
from app.models.campaign import Message, MessageStatus

# Mail priority (lower = higher priority in Lane A)
MAIL_PRIORITY = {
    4: 0,  # M4 highest
    3: 1,
    2: 2,
    1: 3   # M1 lowest
}

class MessageQueue:
    """Dual-lane priority queue per domain."""
    
    def get_due_messages(
        self,
        domain: str,
        current_time: datetime,
        all_messages: List[Message]
    ) -> Tuple[Optional[Message], Optional[Message]]:
        """Select Lane A and Lane B messages for current slot.
        
        Args:
            domain: Domain to check
            current_time: Current datetime
            all_messages: All queued messages for this domain
            
        Returns:
            (lane_a_message, lane_b_message)
            
        Logic:
            Lane A: Highest mail_number (M4 > M3 > M2 > M1) that is due
            Lane B: M1 if available, else lowest mail_number != Lane A
        """
        # Filter to this domain, due, queued status
        due = [
            m for m in all_messages
            if m.domain_used == domain
            and m.scheduled_at <= current_time
            and m.status == MessageStatus.queued
        ]
        
        if not due:
            return None, None
        
        # Sort by priority (highest mail_number first), then lead_id
        due.sort(key=lambda m: (
            MAIL_PRIORITY.get(m.mail_number, 999),
            m.lead_id
        ))
        
        # Lane A: First in sorted list (highest priority)
        lane_a = due[0] if due else None
        
        # Lane B: Prefer M1, else lowest available
        lane_b = None
        
        if lane_a and len(due) > 1:
            # Look for M1 first
            m1_candidates = [m for m in due[1:] if m.mail_number == 1]
            if m1_candidates:
                lane_b = m1_candidates[0]
            else:
                # No M1, pick lowest mail_number != lane_a
                for m in reversed(due[1:]):  # Reversed = lowest priority first
                    if m.mail_number != lane_a.mail_number:
                        lane_b = m
                        break
                
                # If all same mail_number as lane_a, pick second one
                if not lane_b and len(due) > 1:
                    lane_b = due[1]
        
        return lane_a, lane_b
```

---

### **PHASE 3: BACKGROUND WORKER** ⭐ (Prioriteit 2)

#### **3.1 Message Sender Worker**

**File**: `backend/app/services/message_sender.py` (NEW)

```python
"""Background worker for sending messages with dual-lane throttle."""
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from loguru import logger

from app.core.sending_policy import SENDING_POLICY
from app.services.message_queue import MessageQueue, DOMAINS
from app.services.db_campaign_store import campaign_store
from app.schemas.campaign import MessageQuery
from app.models.campaign import MessageStatus

class MessageSenderWorker:
    """Background worker that sends messages according to dual-lane schedule."""
    
    def __init__(self):
        self.queue_manager = MessageQueue()
        self.last_send_time = {}  # domain → last send datetime
    
    def run_once(self):
        """Run one iteration of the sending loop."""
        current_time = datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        # Check if within sending window
        if not SENDING_POLICY.is_valid_sending_day(current_time):
            logger.debug("Not a valid sending day, skipping")
            return
        
        if not self._is_within_sending_hours(current_time):
            logger.debug("Outside sending hours, skipping")
            return
        
        # Process each domain
        for domain in DOMAINS:
            self._process_domain(domain, current_time)
    
    def _is_within_sending_hours(self, dt: datetime) -> bool:
        """Check if within 08:00-17:00 window."""
        hour = dt.hour
        return 8 <= hour < 17
    
    def _process_domain(self, domain: str, current_time: datetime):
        """Process one domain's message queue."""
        
        # Get all queued messages for this domain
        all_messages = campaign_store.list_messages(
            MessageQuery(
                domain_used=domain,
                status=MessageStatus.queued,
                page_size=10000  # Get all
            )
        )
        
        if not all_messages:
            return
        
        # Check throttle (20 min since last send for this domain)
        last_send = self.last_send_time.get(domain)
        if last_send:
            minutes_since = (current_time - last_send).total_seconds() / 60
            if minutes_since < 20:
                logger.debug(f"Domain {domain} throttled ({minutes_since:.1f} min since last)")
                return
        
        # Get Lane A and Lane B messages
        lane_a, lane_b = self.queue_manager.get_due_messages(
            domain,
            current_time,
            all_messages
        )
        
        if not lane_a:
            return
        
        # Send Lane A
        self._send_message(lane_a, "A")
        
        # Send Lane B (if exists)
        if lane_b:
            self._send_message(lane_b, "B")
        
        # Update last send time
        self.last_send_time[domain] = current_time
        
        logger.info(
            f"Sent {domain}: "
            f"Lane A = M{lane_a.mail_number} lead {lane_a.lead_id[:8]}, "
            f"Lane B = {f'M{lane_b.mail_number} lead {lane_b.lead_id[:8]}' if lane_b else 'None'}"
        )
    
    def _send_message(self, message: Message, lane: str):
        """Actually send a message (placeholder for now)."""
        
        # TODO: Integrate with actual SMTP sender
        # For now, just mark as sent
        
        logger.info(
            f"[{lane}] Sending M{message.mail_number} to lead {message.lead_id[:8]} "
            f"via {message.from_email}"
        )
        
        # Update message status
        message.status = MessageStatus.sent
        message.sent_at = datetime.now(ZoneInfo(SENDING_POLICY.timezone))
        
        campaign_store.update_message(message)
        
        # TODO: Check if this was M1/M2/M3, schedule next mail
        # TODO: Check for stops (reply/unsub/bounce)
    
    def run_forever(self, interval_seconds: int = 60):
        """Run worker loop continuously."""
        logger.info("Message sender worker started")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Worker error: {e}")
            
            time.sleep(interval_seconds)


# Singleton instance
worker = MessageSenderWorker()
```

---

### **PHASE 4: STOP CRITERIA ENFORCEMENT** ⭐ (Prioriteit 2)

#### **4.1 Stop Checker**

**File**: `backend/app/services/stop_checker.py` (NEW)

```python
"""Check and enforce stop criteria for leads."""
from typing import List
from loguru import logger

from app.services.leads_store import leads_store
from app.services.db_campaign_store import campaign_store
from app.models.campaign import MessageStatus

def check_and_cancel_future_messages(lead_id: str, after_mail_number: int):
    """Cancel future messages if lead should be stopped.
    
    Args:
        lead_id: Lead UUID
        after_mail_number: Current mail number (cancel > this)
        
    Checks:
        - replied
        - unsubscribed
        - bounced
        
    If any true, cancel M2/M3/M4 (status → canceled)
    """
    lead = leads_store.get_by_id(lead_id)
    if not lead:
        return
    
    should_stop = (
        lead.replied or
        getattr(lead, 'unsubscribed', False) or
        getattr(lead, 'bounced', False)
    )
    
    if not should_stop:
        return
    
    # Get queued messages for this lead (mail_number > current)
    from app.schemas.campaign import MessageQuery
    
    messages = campaign_store.list_messages(
        MessageQuery(
            lead_id=lead_id,
            status=MessageStatus.queued,
            page_size=100
        )
    )
    
    canceled_count = 0
    for msg in messages:
        if msg.mail_number > after_mail_number:
            msg.status = MessageStatus.canceled
            campaign_store.update_message(msg)
            canceled_count += 1
            
            logger.info(
                f"Canceled M{msg.mail_number} for lead {lead_id[:8]} "
                f"(replied={lead.replied}, unsub={getattr(lead, 'unsubscribed', False)}, "
                f"bounced={getattr(lead, 'bounced', False)})"
            )
    
    if canceled_count > 0:
        logger.info(f"Canceled {canceled_count} future messages for lead {lead_id[:8]}")
```

**Integration in `message_sender.py`:**
```python
# In _send_message(), after marking as sent:

def _send_message(self, message: Message, lane: str):
    # ... existing send logic ...
    
    # After sending, check if lead should stop
    from app.services.stop_checker import check_and_cancel_future_messages
    
    check_and_cancel_future_messages(
        lead_id=message.lead_id,
        after_mail_number=message.mail_number
    )
```

---

### **PHASE 5: API UPDATES** ⭐ (Prioriteit 3)

#### **5.1 Remove Campaign-Level Domain**

**File**: `backend/app/api/campaigns.py`

**Change `create_campaign()`:**
```python
# BEFORE:
flow, domain, templates = _assign_next_available_flow(start_at)
campaign.domain = domain  # ❌ Remove this!

# AFTER:
# No domain assignment at campaign level
# Domains are assigned per lead in scheduler
campaign.domain = None  # Or make nullable in schema
```

**Change Campaign model:**
```python
# backend/app/models/campaign.py

class Campaign(SQLModel, table=True):
    # ...
    domain: Optional[str] = Field(
        default=None, 
        sa_column=Column(String, index=True)
    )  # Now optional - domains per lead!
```

#### **5.2 Campaign Detail Response**

**Add schedule preview with domain distribution:**

```python
# In get_campaign_detail():

lead_domain_assignments = {}
for msg in campaign_messages:
    if msg.lead_id not in lead_domain_assignments:
        lead_domain_assignments[msg.lead_id] = msg.domain_used

domain_distribution = {}
for domain in DOMAINS:
    count = sum(1 for d in lead_domain_assignments.values() if d == domain)
    domain_distribution[domain] = count

response["domain_distribution"] = domain_distribution
response["domains_used"] = DOMAINS
```

---

## 📊 **TESTING STRATEGY**

### **Unit Tests**

```python
# tests/test_stream_calculator.py

def test_stream_assignment():
    assert get_stream_for_mail(1) == "A"
    assert get_stream_for_mail(2) == "B"
    assert get_stream_for_mail(3) == "A"
    assert get_stream_for_mail(4) == "B"

def test_snap_to_stream_slot():
    dt = datetime(2025, 10, 13, 8, 15)  # 08:15
    
    # Stream A should snap to 08:20
    snapped_a = snap_to_stream_slot(dt, "A")
    assert snapped_a.minute == 20
    
    # Stream B should snap to 08:30
    snapped_b = snap_to_stream_slot(dt, "B")
    assert snapped_b.minute == 30

# tests/test_lead_domain_assignment.py

def test_modulo_4_pattern():
    lead_ids = [f"lead-{i}" for i in range(1, 21)]
    assignments = assign_lead_domains(lead_ids)
    
    assert assignments["lead-1"] == DOMAINS[0]  # v1
    assert assignments["lead-2"] == DOMAINS[1]  # v2
    assert assignments["lead-3"] == DOMAINS[2]  # v3
    assert assignments["lead-4"] == DOMAINS[3]  # v4
    assert assignments["lead-5"] == DOMAINS[0]  # v1 (wrap)

# tests/test_priority_queue.py

def test_lane_selection():
    queue = MessageQueue()
    
    messages = [
        Message(id="1", mail_number=1, lead_id="lead-a", ...),
        Message(id="2", mail_number=4, lead_id="lead-b", ...),
        Message(id="3", mail_number=2, lead_id="lead-c", ...),
    ]
    
    lane_a, lane_b = queue.get_due_messages("v1", now, messages)
    
    # Lane A should be M4 (highest)
    assert lane_a.mail_number == 4
    
    # Lane B should be M1 (preferred)
    assert lane_b.mail_number == 1
```

---

## 🚀 **DEPLOYMENT CHECKLIST**

### **Pre-Deployment**

- [ ] All unit tests passing
- [ ] Excel reference matches generated schedule
- [ ] Worker can run standalone (not blocking API)
- [ ] Stop criteria tested (cancel M2-M4 on reply)

### **Database Migration**

```sql
-- Make campaign.domain nullable (already done in previous migration)
-- No other schema changes needed!

-- Add index for efficient queue queries
CREATE INDEX IF NOT EXISTS idx_messages_domain_status_scheduled 
ON messages(domain_used, status, scheduled_at);
```

### **Deployment Steps**

1. **Deploy code** to Render
2. **Start worker** as separate process/dyno
3. **Monitor logs** for dual-lane sending
4. **Validate** against Excel schedule

### **Worker Start Command**

```bash
# In Render or separate worker process:
python -c "from app.services.message_sender import worker; worker.run_forever(60)"
```

---

## 📈 **EXPECTED PERFORMANCE**

### **Before (v1.0)**
```
1 domain voor alle leads
27 slots/dag
= 312 dagen voor 2103 leads × 4 mails
```

### **After (v2.2)**
```
4 domains parallel
54 slots/dag/domain (27 vensters × 2 lanes)
= 216 emails/dag total

2103 leads / 4 = ~526 per domain
526 / 54 = ~10 dagen per mail
= ~40 dagen total (M1-M4)

8x sneller! (was 312 → nu 40 dagen)
```

**Met stop criteria (realistic):**
- M1: 100% (2103 leads) = 10 dagen
- M2: ~60% (1262 leads) = 6 dagen
- M3: ~20% (421 leads) = 2 dagen
- M4: ~5% (105 leads) = 1 dag

**Total: ~19 dagen** (vs 312 dagen!)

---

## 🎯 **IMPLEMENTATION ORDER**

1. ✅ **Excel validatie** (DONE)
2. ⭐ **Phase 1**: Stream calculator + lead-domain assignment
3. ⭐ **Phase 2**: Priority queue logic
4. ⭐ **Phase 3**: Background worker (basic send)
5. ⭐ **Phase 4**: Stop criteria enforcement
6. ⭐ **Phase 5**: API updates + tests

**Total effort**: ~8 uur development + 2 uur testing

---

## ❓ **OPEN VRAGEN (GEEN)**

Alle 13 vragen beantwoord! Ready to implement.

**Start implementatie? Zeg "GO" om te beginnen!** 🚀
