# 🧭 CAMPAIGN SCHEDULING ANALYSE - DEEL 1: OVERZICHT

**Datum**: 10 oktober 2025  
**Status**: ANALYSE - GEEN WIJZIGINGEN  

---

## 📊 EXECUTIVE SUMMARY

Je Mail SaaS heeft een **flow-based scheduling systeem**:

### ✅ **Wat ER IS**
- 4 domeinen parallel (v1-v4)
- 4 vaste mails per lead (workday offsets: 0, 3, 6, 9)
- Domain-specific christian@/victor@ aliassen  
- Throttling: 1 mail/20 min per domein
- Werkuren: ma-vr 08:00-17:00
- FIFO queue per domein
- Messages worden **bij campaign creation** direct gepland

### ❌ **Wat ER NIET IS**
- Geen background sender job (messages blijven in queue)
- Geen auto-start op scheduled date
- Geen echte follow-up conditie (reply check)
- Geen domain load balancing binnen campagne
- Geen lead-level domain assignment

---

## 🏗️ ARCHITECTUUR

```
USER → API → FLOWS → SCHEDULER → DB
             ↓        ↓
         versie   berekening   
         mapping  schedules
                     ↓
                  POLICY
                  regels
```

### **Core Modules**

1. **campaign_flows.py**
   - Hard-coded domain→flow mapping
   - Mail schedule berekening (workday offsets)
   - Alias assignment (christian/victor per mail)

2. **campaign_scheduler.py**
   - Message creation voor alle leads × mails
   - FIFO queue management (in-memory)
   - Throttling enforcement
   
3. **sending_policy.py**
   - Hard-coded constraints (niet configureerbaar)
   - Tijdvenster validatie
   - Weekend/werkdag checks

4. **db_campaign_store.py**
   - Database persistence
   - Campaign, audience, messages opslag

---

## 🎯 JOUW CAMPAGNE: WEBSHOP V1

**Created**: 10 okt 2025, 16:36  
**Start**: 12 okt 2025 (zaterdag!)  
**Domain**: punthelder-vindbaarheid.nl (v1)  
**Leads**: 2103  

### **Wat er GEBEURD IS**

```python
# 1. Campaign row created
campaign = Campaign(
    name="Webshop Campaign V1",
    domain="punthelder-vindbaarheid.nl",
    start_at="2025-10-12 08:00",
    status="draft"
)

# 2. Audience snapshot
audience = CampaignAudience(
    campaign_id=campaign.id,
    lead_ids=[...2103 UUIDs...]
)

# 3. Messages created (NU AL!)
for lead in 2103:
    for mail in [1,2,3,4]:
        Message(
            lead_id=lead,
            mail_number=mail,
            scheduled_at=calculated_date,
            status="queued"
        )
# → 8,412 message rows in database
```

### **Actual Schedule**

| Mail | Alias | Offset | Datum |
|------|-------|--------|-------|
| M1 | christian | 0 werkdagen | **Ma 14 okt 08:00** |
| M2 | christian | +3 werkdagen | **Do 17 okt 08:00** |
| M3 | victor | +6 werkdagen | **Ma 21 okt 08:00** |
| M4 | victor | +9 werkdagen | **Do 24 okt 08:00** |

**Waarom niet 12 okt?** → Weekend! Scheduler snapped naar ma 14 okt.

**Doorlooptijd**: 10 kalenderdagen (14-24 okt)

---

## ⏰ WORKDAY OFFSET BEREKENING

### **Algoritme**

```python
def calculate_mail_schedule(start, flow):
    schedule = {}
    
    for step in flow.steps:
        target = start
        workdays_added = 0
        
        # Tel werkdagen vanaf start
        while workdays_added < step.workdays_offset:
            target += 1 day
            if is_werkdag(target):  # ma-vr
                workdays_added += 1
        
        # Snap naar valid slot
        scheduled = get_next_valid_slot(target)
        schedule[step.mail_number] = scheduled
    
    return schedule
```

### **Voorbeeld: Start Zaterdag**

```
Start: za 12 okt 2025

M1 (offset 0):
  za 12 → is weekend
  → snap naar ma 14 okt 08:00

M2 (offset +3):
  ma 14 (dag 1)
  di 15 (dag 2)  
  wo 16 (dag 3)
  → do 17 okt 08:00

M3 (offset +6):
  ma 14, di 15, wo 16, do 17, vr 18, ma 21
  → ma 21 okt 08:00

M4 (offset +9):
  +3 meer werkdagen
  → do 24 okt 08:00
```

### **Weekend/Buiten-Uren Handling**

```python
if is_weekend(date):
    date = next_monday_08:00

if hour < 8:
    hour = 8:00

if hour >= 17:
    date = next_workday_08:00

# Align op 20-min grid
minutes = round_up_to(:00, :20, :40)
```

