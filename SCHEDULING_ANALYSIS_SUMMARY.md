# 🧭 CAMPAIGN SCHEDULING ANALYSE - EXECUTIVE SUMMARY

**Datum**: 10 oktober 2025  
**Campagne**: Webshop Campaign V1  
**Status**: ANALYSE COMPLEET - GEEN WIJZIGINGEN GEDAAN

---

## 📊 HUIDIGE SITUATIE: JOUW CAMPAGNE

### **Wat is Aangemaakt**

```
Campaign ID: abc-123
Name: Webshop Campaign V1
Domain: punthelder-vindbaarheid.nl (v1)
Start: 12 oktober 2025 (zaterdag)
Leads: 2,103
Status: draft

Database:
- 1 campaign row
- 1 audience row (2103 lead IDs)
- 8,412 message rows (2103 × 4 mails)

In-Memory Queue:
- domain_queues["v1"] = 8,412 messages
- active_campaigns["v1"] = "abc-123"
```

### **Actual Schedule (Na Weekend Snap)**

| Mail | Alias | From | Reply-To | Scheduled |
|------|-------|------|----------|-----------|
| M1 | christian | christian@v1 | christian@v1 | **Ma 14 okt 08:00** |
| M2 | christian | christian@v1 | christian@v1 | **Do 17 okt 08:00** |
| M3 | victor | victor@v1 | christian@v1 | **Ma 21 okt 08:00** |
| M4 | victor | victor@v1 | christian@v1 | **Do 24 okt 08:00** |

**Flow duration**: 9 werkdagen (10 kalenderdagen)

---

## ⚠️ KRITIEKE BEVINDING: THROUGHPUT BOTTLENECK

### **Het Probleem**

```
Throttling: 1 email per 20 minuten per domein
Slots/dag: 27 (08:00-16:40)
Alle 2,103 leads op ÉÉN domein (v1)

Berekening per mail:
2,103 leads / 27 slots = 78 dagen

Voor alle 4 mails:
78 × 4 = 312 dagen (!)

Start: 14 oktober 2025
Einde: 20 augustus 2026
```

### **Waarom Dit Gebeurt**

**Domain assignment logica:**
```python
# Bij campaign creation:
domain = _assign_next_available_flow()
# → Alle leads krijgen ZELFDE domein

# Geen load balancing:
for lead in leads:
    message.domain_used = campaign.domain  # Altijd v1!
```

**Design keuze**: Domain consistency voor reply threading  
**Trade-off**: Throughput vs. consistency

---

## 🔄 HOE HET WERKT: STAP-VOOR-STAP

### **1. Campaign Creation → Message Planning**

```
User → API → assign_domain(v1) → get_flow(v1) 
→ calculate_schedule(start=12-okt)
→ snap_to_valid_slot(→ 14-okt ma 08:00)
→ create_messages(2103 × 4 = 8412)
→ save_to_database
→ add_to_queue
```

**Output**: 8,412 rijen in `messages` table, status=`queued`

### **2. Workday Offset Berekening**

```python
Start: za 12 okt 2025

M1 (offset 0):
  weekend → snap naar ma 14 okt 08:00

M2 (offset +3 werkdagen):
  ma 14 (1) + di 15 (2) + wo 16 (3) = do 17 okt 08:00

M3 (offset +6 werkdagen):  
  +3 meer vanaf do 17 = ma 21 okt 08:00

M4 (offset +9 werkdagen):
  +3 meer vanaf ma 21 = do 24 okt 08:00
```

**Regels:**
- Alleen ma-vr (geen weekend)
- Alleen 08:00-17:00 (laatste slot 16:40)
- Align op 20-min grid (:00, :20, :40)

### **3. Domain & Alias Assignment**

**Domain**: Round-robin eerste beschikbare
- Check v1, v2, v3, v4
- Eerste niet-busy domein wins
- ALLE leads op dat domein

**Alias**: Per mail number
- M1, M2: christian
- M3, M4: victor
- Reply-To altijd christian

**Email format:**
```
christian@punthelder-vindbaarheid.nl
victor@punthelder-vindbaarheid.nl
```

### **4. FIFO Queue & Throttling**

**Queue (in-memory):**
```python
domain_queues["v1"] = [
    msg(lead=1, mail=1, scheduled=14-okt-08:00),
    msg(lead=2, mail=1, scheduled=14-okt-08:00),
    ...8412 messages...
]
```

**Throttle check:**
```python
if (now - last_send) < 20 minutes:
    return []  # Still throttled

if now > scheduled_at:
    pop_message()
    send_email()
    update_last_send(now)
```

### **5. ⚠️ MISSING: Verzending**

**Wat ER NIET IS:**
- Geen background sender job
- Geen cron die queue pollt
- Geen automatische email verzending
- Geen status updates naar "sent"

**Messages blijven in queue!**

---

## 📋 WAAR LEEFT DE CODE

### **Core Modules**

| Module | File | Functie |
|--------|------|---------|
| **Flows** | `app/core/campaign_flows.py` | Domain→flow mapping, mail schedule |
| **Scheduler** | `app/services/campaign_scheduler.py` | Message creation, queue, throttle |
| **Policy** | `app/core/sending_policy.py` | Werkuren, weekend, slot validatie |
| **API** | `app/api/campaigns.py` | Campaign CRUD, start trigger |
| **Store** | `app/services/db_campaign_store.py` | Database persistence |

### **Data Locaties**

| Data | Locatie | Jouw Waarde |
|------|---------|-------------|
| Campaign | `campaigns` table | 1 row |
| Audience | `campaign_audience` table | 1 row, 2103 IDs |
| Messages | `messages` table | **8,412 rows** |
| Queue | In-memory `domain_queues` | 8,412 items |
| Domain status | In-memory `active_campaigns` | v1=busy |

---

## 🎯 UI SCHEDULE PREVIEW: WAT TOEVOEGEN

### **Nieuwe API Response Velden**

```json
GET /api/v1/campaigns/{id}

{
  "schedule_preview": {
    // Overview
    "actual_start_date": "2025-10-14",  // Na weekend snap
    "actual_end_date": "2026-08-20",    // 312 dagen later!
    "total_duration_days": 310,
    "workdays_count": 221,
    "weekend_days_skipped": 2,
    
    // Per mail breakdown
    "mail_schedule": [
      {
        "mail_number": 1,
        "alias": "christian",
        "date": "2025-10-14",
        "time": "08:00",
        "weekday": "Monday",
        "leads_count": 2103,
        "estimated_duration_days": 78,
        "from_email": "christian@punthelder-vindbaarheid.nl",
        "reply_to_email": "christian@punthelder-vindbaarheid.nl"
      },
      {
        "mail_number": 2,
        "alias": "christian", 
        "date": "2025-10-17",
        "time": "08:00",
        "weekday": "Thursday",
        "leads_count": 2103,
        "estimated_duration_days": 78
      },
      // M3, M4 similar
    ],
    
    // Queue info
    "queue_status": {
      "domain": "punthelder-vindbaarheid.nl",
      "total_messages": 8412,
      "queued": 8412,
      "sent": 0,
      "failed": 0,
      "next_send_time": "2025-10-14T08:00:00+02:00",
      "is_domain_busy": true,
      "slots_per_day": 27,
      "throttle_minutes": 20
    },
    
    // Throughput estimate
    "throughput_estimate": {
      "leads_per_day": 27,
      "mails_per_day": 27,
      "days_per_mail": 78,
      "total_days": 312,
      "completion_date": "2026-08-20"
    },
    
    // Daily distribution
    "daily_distribution": [
      {
        "date": "2025-10-14",
        "weekday": "Mon",
        "planned": 27,
        "sent": 0,
        "mail_numbers": [1]
      },
      {
        "date": "2025-10-15",
        "weekday": "Tue",
        "planned": 27,
        "sent": 0,
        "mail_numbers": [1]
      },
      // ... 310 dagen
    ]
  }
}
```

### **Backend Implementatie**

```python
# In get_campaign_detail():

# Get all messages
messages = campaign_store.list_messages(
    MessageQuery(campaign_id=campaign_id, page_size=10000)
)

# Group by mail_number
mails_grouped = {}
for msg in messages:
    if msg.mail_number not in mails_grouped:
        mails_grouped[msg.mail_number] = []
    mails_grouped[msg.mail_number].append(msg)

# Build mail schedule
mail_schedule = []
for mail_num in sorted(mails_grouped.keys()):
    msgs = mails_grouped[mail_num]
    first = msgs[0]
    
    # Calculate duration for this mail
    duration_days = len(msgs) / 27  # slots per day
    
    mail_schedule.append({
        "mail_number": mail_num,
        "alias": first.alias,
        "date": first.scheduled_at.date(),
        "leads_count": len(msgs),
        "estimated_duration_days": int(duration_days),
        "from_email": first.from_email
    })

# Calculate throughput
total_messages = len(messages)
queued = len([m for m in messages if m.status == "queued"])
days_to_complete = queued / 27

schedule_preview = {
    "mail_schedule": mail_schedule,
    "throughput_estimate": {
        "days_per_mail": int(queued / 27 / 4),
        "total_days": int(days_to_complete)
    }
}
```

---

## 💡 UI VISUALISATIE OPTIES

### **1. Timeline View (Gantt-style)**

```
Campaign Timeline: Webshop V1
──────────────────────────────────────────────────────────────────
Oct 2025    Nov    Dec    Jan 2026    Feb    ...    Aug
────────────────────────────────────────────────────────────────
M1 ████████████████████████████ (78d)
         M2 ████████████████████████████ (78d)
                  M3 ████████████████████████████ (78d)
                           M4 ████████████████████████████ (78d)
────────────────────────────────────────────────────────────────
```

### **2. Calendar Heat Map**

```
October 2025
Mo  Tu  We  Th  Fr  Sa  Su
              1   2   3   4   5
 6   7   8   9  10  11  12
13 [14] 15  16 [17] 18  19    ← M1 start, M2 start
20 [21] 22  23 [24] 25  26    ← M3 start, M4 start
27  28  29  30  31

Legend:
[14] = Mail starts today
Heat = Number of sends planned
```

### **3. Stats Cards**

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Total Messages  │  │ Estimated Days  │  │ Completion Date │
│   8,412         │  │      312        │  │   20 Aug 2026   │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Mails/Day       │  │ Domain Used     │  │ Throttle        │
│   27 max        │  │   v1 only       │  │   20 min        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### **4. Per-Mail Breakdown Table**

```
Mail  Alias      Date       Time   Leads  Duration  From
────────────────────────────────────────────────────────────
M1    christian  14 Oct     08:00  2103   78 days   christian@v1
M2    christian  17 Oct     08:00  2103   78 days   christian@v1  
M3    victor     21 Oct     08:00  2103   78 days   victor@v1
M4    victor     24 Oct     08:00  2103   78 days   victor@v1
────────────────────────────────────────────────────────────
                                   Total: 312 days
```

### **5. Warning Banner**

```
⚠️  THROUGHPUT WARNING
This campaign will take approximately 312 days to complete due to 
throttling limits (27 emails/day on domain v1).

Consider:
• Split into 4 campaigns across v1-v4 domains (4x faster)
• Reduce lead count per campaign
• Review throttling settings

Estimated completion: 20 August 2026
```

---

## 🚀 AANBEVELINGEN

### **Korte Termijn (Nu)**

**Voor jouw campagne:**

1. **Accept 312 dagen**, OF
2. **Split campaign:**
   ```
   Campaign V1a: 526 leads op v1 domain (78 dagen)
   Campaign V1b: 526 leads op v2 domain (78 dagen)
   Campaign V1c: 526 leads op v3 domain (78 dagen)
   Campaign V1d: 525 leads op v4 domain (78 dagen)
   
   Parallel = 78 dagen totaal (4x sneller!)
   ```

3. **Add UI schedule preview** (deze analyse data)

### **Middellange Termijn (Volgende Sprint)**

1. **Implementeer background sender job**
   ```python
   # Cron elke minuut:
   for domain in ["v1", "v2", "v3", "v4"]:
       messages = scheduler.get_next_messages_to_send(domain)
       for msg in messages:
           send_email(msg)
           update_status(msg, "sent")
   ```

2. **Implementeer open/reply tracking**
   - Pixel tracking voor opens
   - IMAP polling voor replies
   - Update message status

3. **Implementeer echte follow-up**
   - Trigger na M4 sent + no reply
   - Auto-schedule M5
   - Conditional logic

### **Lange Termijn (Future)**

1. **Lead-level domain distribution**
   ```python
   for i, lead in enumerate(leads):
       domain = domains[i % 4]  # Round-robin
       # 4x throughput improvement!
   ```

2. **Configureerbare throttling**
   ```python
   # UI setting:
   slot_every_minutes = 5  # Was: 20
   # 4x meer slots per dag
   ```

3. **Queue monitoring dashboard**
   - Real-time queue size
   - Send rate graphs
   - Domain utilization

---

## 📊 CONCLUSIE

### **Wat GOED werkt**

✅ **Flow-based scheduling** - Clean, voorspelbaar  
✅ **Workday offset logic** - Correct geïmplementeerd  
✅ **Domain-specific aliassen** - Per domain configuratie  
✅ **Message persistence** - Alles in database  
✅ **FIFO queue** - Fair ordering  
✅ **Weekend handling** - Snaps correct naar maandag

### **Wat ONTBREEKT**

❌ **Background sender** - Messages blijven in queue  
❌ **Lead-level balancing** - Alle leads op 1 domein  
❌ **Follow-up conditie** - Geen reply check  
❌ **Schedule preview UI** - Geen inzicht voor user  
❌ **Queue monitoring** - Geen real-time status

### **Impact Jouw Campagne**

```
Status: Messages GEPLAND maar NIET auto-verzonden
Throughput: 27 mails/dag (bottleneck!)
Duration: 312 dagen (10+ maanden)
Action needed: Split of accept lange doorlooptijd
```

### **Next Steps**

**Prioriteit 1**: Schedule preview in UI (deze data)  
**Prioriteit 2**: Background sender job  
**Prioriteit 3**: Domain balancing strategie  

---

**📄 Volledige documentatie**: Zie PART1, PART2, PART3 voor technische details

