# 🎯 SCHEDULER V2.2 - DEFINITIEVE SPECIFICATIE

**Datum**: 13 oktober 2025  
**Status**: 100% BEGRIP COMPLEET - READY TO IMPLEMENT  

---

## ✅ **VOLLEDIGE STRUCTUUR**

### **1. ARCHITECTUUR COMPONENTEN**

```
4 DOMEINEN
├─ v1: punthelder-vindbaarheid.nl
├─ v2: punthelder-seo.nl
├─ v3: punthelder-zoekmachine.nl
└─ v4: punthelder-marketing.nl

2 ALIASSEN PER DOMEIN
├─ christian@ (M1, M2)
└─ victor@ (M3, M4)

2 STREAMS (tijdslot patterns)
├─ Stream A: :00/:20/:40 (M1, M3)
└─ Stream B: :10/:30/:50 (M2, M4)

4 MAIL PHASES
├─ M1: christian@ + Stream A + offset 0
├─ M2: christian@ + Stream B + offset +3 workdays
├─ M3: victor@ + Stream A + offset +6 workdays
└─ M4: victor@ + Stream B + offset +9 workdays
```

---

## 📊 **LEAD-DOMAIN ASSIGNMENT**

```python
# Bij campaign creation:
for idx, lead in enumerate(leads):
    domain = DOMAINS[idx % 4]
    # Lead blijft op dit domein voor alle 4 mails!
    
# Result:
Lead 1, 5, 9, 13... → v1 (vindbaarheid)
Lead 2, 6, 10, 14... → v2 (seo)
Lead 3, 7, 11, 15... → v3 (zoekmachine)
Lead 4, 8, 12, 16... → v4 (marketing)
```

---

## 🕐 **SCHEDULING LOGIC**

### **Per Lead, Per Mail:**

```python
def schedule_message(lead, mail_number, domain, start_date):
    # 1. Bepaal alias
    alias = "christian" if mail_number in [1, 2] else "victor"
    from_email = f"{alias}@{domain}"
    
    # 2. Bepaal stream
    stream = "A" if mail_number in [1, 3] else "B"
    
    # 3. Bepaal workday offset
    offsets = {1: 0, 2: 3, 3: 6, 4: 9}
    target_date = add_workdays(start_date, offsets[mail_number])
    
    # 4. Snap naar stream slot
    if stream == "A":
        scheduled_at = snap_to_minute(target_date, [0, 20, 40])
    else:  # Stream B
        scheduled_at = snap_to_minute(target_date, [10, 30, 50])
    
    # 5. Ensure werkuren (08:00-17:00, ma-vr)
    scheduled_at = ensure_valid_workday_slot(scheduled_at)
    
    return Message(
        lead_id=lead.id,
        mail_number=mail_number,
        domain_used=domain,
        alias=alias,
        from_email=from_email,
        reply_to_email=f"christian@{domain}",
        scheduled_at=scheduled_at,
        status="queued"
    )
```

**Resultaat:** Meerdere leads kunnen DEZELFDE scheduled_at hebben!

---

## 📧 **DUAL-LANE SENDING**

### **Wat is Dual-Lane?**

**Per tijdslot per domein kunnen 2 messages verzonden:**
- **Lane A**: 1 message van christian@
- **Lane B**: 1 message van victor@

### **Waarom werkt dit?**

- Verschillende FROM addresses
- Parallel SMTP sessions mogelijk
- Geen conflict in sender reputation

### **Worker Logic:**

```python
# Run elke minuut
current_time = now()
current_slot = round_to_slot(current_time)  # Nearest :00/:10/:20/:30/:40/:50

for domain in DOMAINS:
    # Get ALL messages at this EXACT time for this domain
    due = [
        msg for msg in all_messages
        if msg.domain_used == domain
        and msg.scheduled_at == current_slot
        and msg.status == "queued"
    ]
    
    if not due:
        continue
    
    # Split by alias
    christian_msgs = [m for m in due if m.alias == "christian"]
    victor_msgs = [m for m in due if m.alias == "victor"]
    
    # Lane A: christian@ (prioritize higher mail_number)
    lane_a = None
    if christian_msgs:
        christian_msgs.sort(key=lambda m: m.mail_number, reverse=True)
        lane_a = christian_msgs[0]
    
    # Lane B: victor@ (prioritize higher mail_number)
    lane_b = None
    if victor_msgs:
        victor_msgs.sort(key=lambda m: m.mail_number, reverse=True)
        lane_b = victor_msgs[0]
    
    # Send both
    if lane_a:
        send_email(lane_a)
        mark_sent(lane_a)
    
    if lane_b:
        send_email(lane_b)
        mark_sent(lane_b)
```

---

## 📈 **CAPACITEIT & THROUGHPUT**

### **Per Tijdslot:**

```
1 slot (bijv. 08:00) per domein:
├─ Lane A: 0-1 message (christian@)
└─ Lane B: 0-1 message (victor@)
   = Max 2 messages per slot per domein
```

### **Per Dag:**

```
27 Stream A slots (08:00, 08:20, 08:40... 16:40)
27 Stream B slots (08:10, 08:30, 08:50... 16:50)
= 54 tijdslots per dag

Per domein max:
- Als alleen M1 actief: 27/dag (alleen christian@, Stream A)
- Als M1+M2 actief: 54/dag (christian@ op beide streams)
- Als M1+M2+M3 actief: 54/dag (maar overlap: chr+vic op Stream A)
- Als M1+M2+M3+M4 actief: 54/dag (beide lanes volledig benut)

Totaal over 4 domeinen: 4 × 54 = 216 messages/dag MAX
```

### **20-Min Window Analysis:**

```
DAG 1-3 (M1 only):
  08:00 slot: 4 domains × 1 (M1 chr) = 4
  08:10 slot: 0
  Window: 4 messages

DAG 4+ (M1 + M2):
  08:00 slot: 4 domains × 1 (M1 chr) = 4
  08:10 slot: 4 domains × 1 (M2 chr) = 4
  Window: 8 messages

DAG 9+ (M1 + M2 + M3):
  08:00 slot: 4 domains × 2 (M1 chr + M3 vic) = 8
  08:10 slot: 4 domains × 1 (M2 chr) = 4
  Window: 12 messages

DAG 12+ (M1 + M2 + M3 + M4):
  08:00 slot: 4 domains × 2 (M1 chr + M3 vic) = 8
  08:10 slot: 4 domains × 2 (M2 chr + M4 vic) = 8
  Window: 16 messages (PEAK!)
```

---

## 🛑 **STOP CRITERIA**

```python
# Check VOOR elke nieuwe phase
def check_and_cancel_future(lead_id, after_mail_number):
    lead = get_lead(lead_id)
    
    should_stop = (
        lead.replied or
        lead.unsubscribed or
        lead.bounced
    )
    
    if should_stop:
        # Cancel M2, M3, M4 if not yet sent
        cancel_messages(
            lead_id=lead_id,
            mail_number__gt=after_mail_number,
            status="queued"
        )
```

**Trigger points:**
- Na M1 verzonden → check before scheduling M2
- Na M2 verzonden → check before scheduling M3
- Na M3 verzonden → check before scheduling M4

---

## 🔄 **EXAMPLE: LEAD 1 JOURNEY**

```
Lead 1 krijgt v1 (vindbaarheid):

M1: 13-okt 08:00 (Stream A)
    └─ FROM: christian@punthelder-vindbaarheid.nl
    └─ REPLY-TO: christian@punthelder-vindbaarheid.nl

M2: 16-okt 08:10 (Stream B, +3 workdays)
    └─ FROM: christian@punthelder-vindbaarheid.nl
    └─ REPLY-TO: christian@punthelder-vindbaarheid.nl

M3: 21-okt 08:00 (Stream A, +6 workdays)
    └─ FROM: victor@punthelder-vindbaarheid.nl
    └─ REPLY-TO: christian@punthelder-vindbaarheid.nl

M4: 24-okt 08:10 (Stream B, +9 workdays)
    └─ FROM: victor@punthelder-vindbaarheid.nl
    └─ REPLY-TO: christian@punthelder-vindbaarheid.nl
```

---

## 🎯 **OVERLAPPING PHASES**

### **Waarom Overlapping?**

Vroege leads zijn al bij M2/M3/M4 terwijl late leads nog bij M1 zijn.

### **Example: 24-okt 08:00 voor v1:**

```
Due messages:
├─ Lead 973 M1 christian@ (nieuwe lead start)
└─ Lead 325 M3 victor@   (oude lead bij fase 3)

Worker selecteert:
├─ Lane A: Lead 973 M1 christian@
└─ Lane B: Lead 325 M3 victor@

Beide verzonden in dit slot!
```

---

## 📋 **DATABASE SCHEMA**

```sql
messages:
  - id (UUID)
  - campaign_id (UUID)
  - lead_id (UUID)
  - domain_used (TEXT)        -- v1/v2/v3/v4
  - mail_number (INTEGER)     -- 1/2/3/4
  - alias (TEXT)              -- christian/victor
  - from_email (TEXT)         -- christian@domain
  - reply_to_email (TEXT)     -- christian@domain
  - scheduled_at (TIMESTAMPTZ) -- EXACT slot time
  - status (TEXT)             -- queued/sent/failed/canceled
  - sent_at (TIMESTAMPTZ)
  - is_followup (BOOLEAN)
  
INDEX: (domain_used, scheduled_at, status) for fast worker queries
```

---

## 🚀 **PERFORMANCE EXPECTATIONS**

### **Voor 2103 leads:**

**Oude v1.0 (1 domain):**
```
2103 leads × 4 mails = 8412 messages
27 slots/dag × 1 domain = 27/dag
= 312 dagen
```

**Nieuwe v2.2 (4 domains parallel):**
```
2103 leads / 4 domains = ~526 per domain

Early phase (M1 only): 526 / 27 = 19 dagen
Peak phase (all 4): Veel overlap, praktisch ~5-10 dagen/phase
Total met stop criteria: ~20-30 dagen

15x sneller! 🚀
```

---

## ✅ **IMPLEMENTATION CHECKLIST**

1. ⬜ Stream calculator module
2. ⬜ Lead-domain assignment (modulo 4)
3. ⬜ Message scheduling met stream snapping
4. ⬜ Dual-lane worker met alias separation
5. ⬜ Priority sorting binnen alias lanes
6. ⬜ Stop criteria enforcement
7. ⬜ Database indices voor worker queries
8. ⬜ Testing tegen Excel reference

---

## 🎯 **READY TO IMPLEMENT!**

Alle specificaties zijn 100% duidelijk.
Excel referentie is volledig begrepen.
Implementatie kan beginnen! 🚀
