# 🧭 CAMPAIGN SCHEDULING ANALYSE - DEEL 3: FOLLOW-UPS & DATABASE

---

## 📨 FOLLOW-UP SYSTEEM

### **Type 1: Flow "Follow-ups" (M2-M4)**

⚠️ **Misleidende naamgeving!** Deze zijn GEEN echte follow-ups.

```python
# In Message model:
is_followup = (mail_number > 1)
# → M2, M3, M4 krijgen is_followup=True
```

**Kenmerken:**
- ✅ Deel van hoofd-flow
- ✅ Automatisch gepland bij creation
- ✅ GEEN conditie (reply niet gecheckt)
- ✅ Fixed timing (workday offsets)
- ❌ NIET afhankelijk van M1 resultaat

**Voor jouw campagne:**
```
M1 (mail_number=1, is_followup=False)
M2 (mail_number=2, is_followup=True)   ← NIET conditoneel!
M3 (mail_number=3, is_followup=True)   ← NIET conditioneel!
M4 (mail_number=4, is_followup=True)   ← NIET conditioneel!
```

**Alle 8,412 messages zijn NU AL gepland**, ongeacht wat er met M1 gebeurt!

---

### **Type 2: Extra Follow-up (Na M4)**

**Dit is de ECHTE follow-up uit campaign settings!**

```python
# Campaign model:
followup_enabled = True
followup_days = 3
followup_attach_report = False
```

**Hoe het ZOU moeten werken:**

```python
# Trigger: NA M4 verzonden + GEEN reply
if m4.sent_at and not lead.replied:
    followup_date = m4.sent_at + timedelta(days=3)
    followup_slot = get_next_valid_slot(followup_date)
    
    Message(
        campaign_id=campaign.id,
        lead_id=lead.id,
        mail_number=5,  # Extra mail!
        scheduled_at=followup_slot,
        is_followup=True,
        parent_message_id=m4.id
    )
```

**Huidige status:**

❌ **NIET GEÏMPLEMENTEERD**
- Geen trigger na M4 send
- Geen reply status check
- Geen automatische M5 scheduling
- Code bestaat (`schedule_followup()`) maar wordt **NIET AANGEROEPEN**

**Wat UI toont:**
```
Follow-up Status
Follow-ups Enabled: No  ← Hard-coded False in creation
```

**Implementatie gap:**
```python
# Missing:
1. Background job die M4 sends monitort
2. Reply detection & lead.replied update
3. Trigger voor schedule_followup()
4. M5 message creation
```

---

## 🗄️ DATABASE SCHEMA

### **Table: campaigns**

```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    template_id UUID NULL,
    domain TEXT NOT NULL,
    start_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    
    -- Follow-up settings (NOT USED YET)
    followup_enabled BOOLEAN DEFAULT TRUE,
    followup_days INTEGER DEFAULT 3,
    followup_attach_report BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_campaigns_domain ON campaigns(domain);
CREATE INDEX idx_campaigns_status ON campaigns(status);
```

**Jouw row:**
```json
{
  "id": "abc-123",
  "name": "Webshop Campaign V1",
  "domain": "punthelder-vindbaarheid.nl",
  "start_at": "2025-10-12T08:00:00+02:00",
  "status": "draft",
  "followup_enabled": true,
  "followup_days": 3
}
```

---

### **Table: campaign_audience**

```sql
CREATE TABLE campaign_audience (
    id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES campaigns(id),
    lead_ids JSONB NOT NULL,
    exclude_suppressed BOOLEAN DEFAULT TRUE,
    exclude_recent_days INTEGER DEFAULT 90,
    one_per_domain BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL
);
```

**Jouw row:**
```json
{
  "campaign_id": "abc-123",
  "lead_ids": ["uuid1", "uuid2", ..., "uuid2103"],
  "exclude_suppressed": true,
  "one_per_domain": true
}
```

**Lead_ids**: Snapshot! Niet live query.

---

### **Table: messages**

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES campaigns(id),
    lead_id UUID REFERENCES leads(id),
    
    -- Scheduling
    domain_used TEXT NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    
    -- Flow metadata
    mail_number INTEGER DEFAULT 1,
    alias TEXT DEFAULT 'christian',
    from_email TEXT,
    reply_to_email TEXT,
    
    -- Status
    status TEXT NOT NULL,
    last_error TEXT,
    open_at TIMESTAMPTZ,
    
    -- Follow-up relationship
    parent_message_id UUID REFERENCES messages(id),
    is_followup BOOLEAN DEFAULT FALSE,
    
    -- Retry & tracking
    retry_count INTEGER DEFAULT 0,
    smtp_message_id TEXT UNIQUE,
    x_campaign_message_id TEXT,
    
    -- Assets
    with_image BOOLEAN DEFAULT FALSE,
    with_report BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_messages_scheduled ON messages(scheduled_at);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_campaign ON messages(campaign_id);
CREATE INDEX idx_messages_lead ON messages(lead_id);
```

**Jouw rows (8,412x):**
```json
// Lead 1, M1
{
  "id": "msg-001",
  "campaign_id": "abc-123",
  "lead_id": "lead-1",
  "domain_used": "punthelder-vindbaarheid.nl",
  "scheduled_at": "2025-10-14T08:00:00+02:00",
  "sent_at": null,
  "mail_number": 1,
  "alias": "christian",
  "from_email": "christian@punthelder-vindbaarheid.nl",
  "reply_to_email": "christian@punthelder-vindbaarheid.nl",
  "status": "queued",
  "is_followup": false
}

// Lead 1, M2
{
  "id": "msg-002",
  "lead_id": "lead-1",
  "scheduled_at": "2025-10-17T08:00:00+02:00",
  "mail_number": 2,
  "alias": "christian",
  "status": "queued",
  "is_followup": true  // ⚠️ Confusing!
}

// ... 8410 more
```

---

## 🔄 DATASTROOM END-TO-END

```
┌─────────────────────────┐
│ 1. USER                 │
│ POST /campaigns         │
│ {name, list, date}      │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 2. API                  │
│ _assign_next_domain()   │
│ → v1 available          │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 3. DATABASE             │
│ INSERT campaigns        │
│ INSERT audience         │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 4. FLOWS                │
│ get_flow_for_domain()   │
│ → CampaignFlow(v1)      │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 5. SCHEDULER            │
│ calculate_mail_schedule │
│ {1: 14-okt, 2: 17-okt}  │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 6. MESSAGES             │
│ FOR lead × mail:        │
│   INSERT messages       │
│ → 8412 rows             │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 7. QUEUE (In-Memory)    │
│ domain_queues["v1"]     │
│ = [8412 messages]       │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 8. ⚠️ MISSING            │
│ Background Sender Job   │
│ - Poll queue            │
│ - Send emails           │
│ - Update status         │
└─────────────────────────┘
```

---

## ⚠️ MISSING: SENDER JOB

### **Wat ER NIET IS**

**Geen automatische verzending!**

Messages zitten in:
1. ✅ Database (`messages` table)
2. ✅ In-memory queue (`domain_queues`)
3. ❌ **MAAR**: Niemand haalt ze eruit!

**Ontbrekende componenten:**

```python
# 1. Cron/Scheduler
# Elke 1 minuut:
for domain in domains:
    messages = get_next_messages_to_send(domain)
    for msg in messages:
        send_email(msg)
        update_status(msg, "sent")

# 2. Email Sender
def send_email(message):
    # SMTP connection
    # Template rendering
    # Send
    # Track SMTP message ID

# 3. Status Updater  
def update_status(message_id, status):
    UPDATE messages 
    SET status = status, sent_at = NOW()
    WHERE id = message_id

# 4. Open Tracker
# Pixel tracking → UPDATE open_at

# 5. Reply Detector
# IMAP inbox → Link replies → UPDATE lead.replied

# 6. Follow-up Trigger
# Check M4 sent + no reply → schedule M5
```

### **Implicaties**

**Voor jouw campagne:**
- ✅ 8,412 messages zijn **gepland** (in DB)
- ✅ Queue is **gevuld** (in memory)
- ❌ **MAAR**: Ze worden **niet verzonden**
- ❌ Start datum (12 okt) wordt **niet gerespecteerd**

**Handmatig starten vereist:**
```python
# Ergens moet je callen:
scheduler.get_next_messages_to_send("v1", now())
# En dan zelf versturen
```

**Of**: Background job implementeren

---

## 🎯 UI/API DATA VOOR SCHEDULE PREVIEW

### **Wat API NU returnt**

```json
GET /api/v1/campaigns/{id}

{
  "id": "abc-123",
  "domain": "punthelder-vindbaarheid.nl",
  "start_at": "2025-10-12T08:00:00+02:00",
  "status": "draft",
  
  "kpis": {
    "total_planned": 8412,
    "total_sent": 0,
    "open_rate": 0.0
  },
  
  "timeline": [],  // Empty tot messages sent
  
  "flow_version": 1,
  "templates": ["v1m1", "v1m2", "v1m3", "v1m4"],
  "estimated_duration_days": 9,
  "audience_count": 2103
}
```

### **Wat ONTBREEKT voor Schedule Preview**

**Nieuwe velden toevoegen:**

```json
{
  "schedule_preview": {
    // Mail schedule
    "first_send_date": "2025-10-14T08:00:00+02:00",
    "last_send_date": "2025-10-24T16:40:00+02:00",
    "total_duration_days": 10,
    "workdays_count": 9,
    
    // Per mail info
    "mail_schedule": [
      {
        "mail_number": 1,
        "alias": "christian",
        "scheduled_date": "2025-10-14",
        "scheduled_time": "08:00",
        "message_count": 2103,
        "from": "christian@punthelder-vindbaarheid.nl"
      },
      {
        "mail_number": 2,
        "alias": "christian",
        "scheduled_date": "2025-10-17",
        "scheduled_time": "08:00",
        "message_count": 2103
      },
      // ...
    ],
    
    // Queue status
    "queue_status": {
      "total_queued": 8412,
      "total_sent": 0,
      "next_send_time": "2025-10-14T08:00:00+02:00",
      "estimated_completion": "2026-08-20"  // 312 dagen!
    },
    
    // Domain status
    "domain_status": {
      "domain": "punthelder-vindbaarheid.nl",
      "is_busy": true,
      "active_campaign_id": "abc-123",
      "queue_size": 8412,
      "slots_per_day": 27,
      "estimated_days_to_complete": 312
    }
  }
}
```

### **Backend Query Hiervoor**

```python
# In get_campaign_detail endpoint:

# Get messages grouped by mail_number
messages_by_mail = {}
for msg in campaign_messages:
    if msg.mail_number not in messages_by_mail:
        messages_by_mail[msg.mail_number] = []
    messages_by_mail[msg.mail_number].append(msg)

# Build mail schedule
mail_schedule = []
for mail_num in sorted(messages_by_mail.keys()):
    msgs = messages_by_mail[mail_num]
    first_msg = msgs[0]
    
    mail_schedule.append({
        "mail_number": mail_num,
        "alias": first_msg.alias,
        "scheduled_date": first_msg.scheduled_at.date(),
        "message_count": len(msgs),
        "from": first_msg.from_email
    })

# Calculate completion estimate
queued_count = len([m for m in messages if m.status == "queued"])
completion_days = queued_count / 27  # slots per day

schedule_preview = {
    "mail_schedule": mail_schedule,
    "queue_status": {
        "total_queued": queued_count,
        "estimated_days_to_complete": completion_days
    }
}
```

---

## 📋 SAMENVATTING: WAAR LEEFT DE CODE

### **Modules & Functies**

| Component | File | Key Functions |
|-----------|------|---------------|
| **Flow Definitie** | `campaign_flows.py` | `get_flow_for_domain()`, `calculate_mail_schedule()` |
| **Scheduler** | `campaign_scheduler.py` | `schedule_campaign()`, `get_next_messages_to_send()` |
| **Policy** | `sending_policy.py` | `get_next_valid_slot()`, `is_valid_sending_day()` |
| **API** | `api/campaigns.py` | `create_campaign()`, `_start_campaign()` |
| **Store** | `db_campaign_store.py` | `create_campaign()`, `create_messages()` |
| **Models** | `models/campaign.py` | `Campaign`, `Message`, `CampaignAudience` |

### **Database Tables**

| Table | Purpose | Jouw Data |
|-------|---------|-----------|
| `campaigns` | Campaign metadata | 1 row |
| `campaign_audience` | Lead snapshot | 1 row, 2103 lead IDs |
| `messages` | Scheduled sends | **8,412 rows** |
| `message_events` | Open/click tracking | 0 rows (nog niet verzonden) |

### **In-Memory State**

| Variable | Locatie | Inhoud |
|----------|---------|--------|
| `domain_queues` | `CampaignScheduler` | 8,412 messages voor v1 |
| `domain_last_send` | `CampaignScheduler` | Laatste send tijd per domein |
| `active_campaigns` | `CampaignScheduler` | {"v1": "abc-123"} |

---

## 🎯 CONCLUSIE

**Je scheduling systeem werkt goed voor:**
- ✅ Flow-based planning
- ✅ Workday offset berekening
- ✅ Domain-specific aliassen
- ✅ Message persistence

**Maar heeft gaps:**
- ❌ Geen background sender
- ❌ Bottleneck: 1 domein voor alle leads
- ❌ Extra follow-up niet geïmplementeerd
- ❌ Geen schedule preview in UI

**Volgende stappen:**
1. Implementeer background sender job
2. Of: Maak 4 separate campaigns (1 per domein)
3. Voeg schedule preview toe aan API/UI
4. Implement echte follow-up conditie

