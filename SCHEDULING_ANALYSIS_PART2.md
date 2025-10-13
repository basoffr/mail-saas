# 🧭 CAMPAIGN SCHEDULING ANALYSE - DEEL 2: DOMEIN & THROTTLING

---

## 🌐 DOMEIN & ALIAS SELECTIE

### **Domain Assignment**

**Bij campaign creation:**
```python
def _assign_next_available_flow(start_at):
    flows = {
        "punthelder-vindbaarheid.nl": flow_v1,
        "punthelder-marketing.nl": flow_v2,
        "punthelder-seo.nl": flow_v3,
        "punthelder-zoekmachine.nl": flow_v4
    }
    
    # Try each in order
    for domain, flow in flows.items():
        if not is_domain_busy(domain):
            return flow, domain
    
    raise Error("All domains busy")
```

### **Kenmerken**

✅ **1 campagne per domein tegelijk**
- Check: `active_campaigns[domain] == campaign_id`
- Geen concurrency binnen 1 domein

✅ **Round-robin eerste beschikbare**
- v1 → v2 → v3 → v4
- Niet: random, hash, load-balanced

❌ **GEEN multi-domain binnen campagne**
- Alle 2103 leads = zelfde domein
- Niet: lead 1 = v1, lead 2 = v2, etc.

❌ **GEEN domain rotation per lead**
- Lead krijgt 4 mails van ZELFDE domein
- Niet: M1 = v1, M2 = v2

### **Voor Jouw Campagne**

```
Domain: punthelder-vindbaarheid.nl (v1)

Alle 2103 leads:
- M1: christian@punthelder-vindbaarheid.nl
- M2: christian@punthelder-vindbaarheid.nl  
- M3: victor@punthelder-vindbaarheid.nl
- M4: victor@punthelder-vindbaarheid.nl
```

**Reden**: Domain consistency voor reply threading!

---

## 👥 ALIAS ASSIGNMENT

### **Hard-coded Flows**

```python
DOMAIN_FLOWS = {
    "punthelder-vindbaarheid.nl": CampaignFlow(
        version=1,
        steps=[
            FlowStep(mail=1, alias="christian", offset=0),
            FlowStep(mail=2, alias="christian", offset=3),
            FlowStep(mail=3, alias="victor", offset=6),
            FlowStep(mail=4, alias="victor", offset=9),
        ]
    ),
    # v2-v4: IDENTIEK, andere domeinen
}
```

### **Email Headers Per Mail**

```python
def get_followup_headers(mail_number, domain):
    if mail_number in [3, 4]:  # Victor
        return {
            "from": f"victor@{domain}",
            "reply_to": f"christian@{domain}"
        }
    else:  # Christian
        return {
            "from": f"christian@{domain}",
            "reply_to": f"christian@{domain}"
        }
```

**Resultaat voor v1:**

| Mail | From | Reply-To | Reden |
|------|------|----------|-------|
| M1 | christian@v1 | christian@v1 | Initieel contact |
| M2 | christian@v1 | christian@v1 | Opvolging Christian |
| M3 | victor@v1 | christian@v1 | Victor neemt over, replies naar Christian |
| M4 | victor@v1 | christian@v1 | Victor laatste poging, replies naar Christian |

**Design keuze**: Replies worden ALTIJD naar Christian gerouteerd voor consistency!

---

## 🚦 THROTTLING & QUEUEING

### **Sending Policy (Hard-coded)**

```python
class SendingPolicy:
    timezone = "Europe/Amsterdam"
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    window_from = "08:00"
    window_to = "17:00"      # Laatste slot: 16:40
    grace_to = "18:00"       # Grace voor delays
    slot_every_minutes = 20
    daily_cap_per_domain = 27
    throttle_scope = "per_domain"
```

### **Slots Per Dag**

```
08:00, 08:20, 08:40, 09:00, 09:20, ...
16:00, 16:20, 16:40
```

**Totaal**: 27 slots  
**Theorie**: 27 emails/dag per domein  
**4 domeinen**: 108 emails/dag max  
**Per uur**: 12 emails (3 per domein)

### **FIFO Queue (In-Memory)**

```python
class CampaignScheduler:
    def __init__(self):
        self.domain_queues = {}
        # {
        #   "v1": [msg1, msg2, ...],
        #   "v2": [...]
        # }
        
        self.domain_last_send = {}
        # {"v1": datetime(2025, 10, 14, 8, 20)}
        
        self.active_campaigns = {}
        # {"v1": "campaign_uuid"}
```

### **Queue Pop Logic**

```python
def get_next_messages_to_send(domain, current_time):
    # 1. Check grace period (< 18:00?)
    if current_time.hour >= 18:
        move_to_next_day(domain)
        return []
    
    # 2. Check throttle (20 min sinds laatste?)
    last_send = domain_last_send[domain]
    if (current_time - last_send).minutes < 20:
        return []  # Still throttled
    
    # 3. Get ready messages (FIFO)
    queue = domain_queues[domain]
    ready = []
    
    while queue:
        item = queue[0]
        if item.scheduled_at <= current_time:
            ready.append(item.message)
            queue.pop(0)  # Remove from front
            domain_last_send[domain] = current_time
        else:
            break  # No more ready
    
    return ready
```

### **Voor Jouw Campagne**

**Queue na creation:**
```
domain_queues["v1"] = [
    # 2103 messages voor M1 (14 okt 08:00)
    msg(lead=1, mail=1, scheduled=14-okt-08:00),
    msg(lead=2, mail=1, scheduled=14-okt-08:00),
    ...
    msg(lead=2103, mail=1, scheduled=14-okt-08:00),
    
    # 2103 messages voor M2 (17 okt 08:00)
    msg(lead=1, mail=2, scheduled=17-okt-08:00),
    ...
    
    # 2103 messages voor M3 (21 okt 08:00)
    ...
    
    # 2103 messages voor M4 (24 okt 08:00)
    ...
]
```

**Totaal in queue**: 8,412 messages

**Verzendtijd theoretisch**:
- 2103 leads / 27 slots per dag = **78 dagen** per mail
- Voor alle 4 mails: **312 dagen** (!)

⚠️ **PROBLEEM**: Queue is veel te groot voor 1 domein!

---

## ⚠️ KRITIEKE BEVINDINGEN

### **Bottleneck: Single Domain**

**Huidige situatie:**
- 2103 leads op 1 domein (v1)
- 27 slots/dag = 27 emails/dag
- 2103 / 27 = **78 dagen** voor M1 alleen
- **312 dagen totaal** voor alle 4 mails

**Oorzaak:**
- Geen load balancing over domeinen
- Alle leads op zelfde domein toegewezen
- Domain remains "busy" tijdens hele campagne

### **Oplossing (Toekomst)**

**Optie 1: Lead-level domain distribution**
```python
# Bij message creation:
for i, lead in enumerate(leads):
    domain = domains[i % 4]  # Round-robin
    # lead 0,4,8 → v1
    # lead 1,5,9 → v2
    # etc.
```

**Resultaat**: 4x sneller (78 dagen → 20 dagen per mail)

**Optie 2: Verhoog throttle**
```python
slot_every_minutes = 5  # Was: 20
daily_cap_per_domain = 108  # Was: 27
```

**Resultaat**: 4x meer capacity per domein

### **Waarom Niet Geïmplementeerd?**

**Design keuze**: Domain consistency
- Lead moet alle 4 mails van ZELFDE domein krijgen
- Reply threading werkt beter
- Sender reputation per domein

**Trade-off**: Throughput vs. consistency

---

## 📊 THROUGHPUT BEREKENINGEN

### **Scenario 1: Huidige Setup (1 domein)**

```
Slots: 27/dag
Leads: 2103
Mails: 4

M1: 2103 / 27 = 78 dagen
M2: 78 dagen  
M3: 78 dagen
M4: 78 dagen

Totaal: 312 dagen (!)
```

### **Scenario 2: 4 Domeinen Parallel**

```
Als leads verdeeld over 4 domeinen:
- v1: 526 leads
- v2: 526 leads
- v3: 526 leads  
- v4: 525 leads

Per domein:
M1: 526 / 27 = 20 dagen

Totaal: 80 dagen (4x sneller)
```

### **Scenario 3: Verhoogde Throttle**

```
slot_every_minutes = 5 (was 20)
slots_per_dag = 108 (was 27)

M1: 2103 / 108 = 20 dagen

Totaal: 80 dagen
```

### **Scenario 4: Ideaal (Beide)**

```
4 domeinen + 5 min throttle:
Per domein: 526 / 108 = 5 dagen
Totaal: 20 dagen

→ 15x sneller dan huidige setup!
```

---

## 🎯 AANBEVELINGEN

### **Voor Jouw Campagne**

**Korte termijn:**
1. Accept 312 dagen doorlooptijd
2. Of: split campagne in 4 kleinere (526 leads elk)
3. Elk op ander domein (v1, v2, v3, v4)

**Lange termijn:**
1. Implementeer lead-level domain distribution
2. Verhoog throttle (5 min ipv 20 min)
3. Test sender reputation impact

**Trade-offs bewust maken:**
- Throughput vs. domain consistency
- Snelheid vs. reply threading
- Parallellisme vs. simpliciteit

