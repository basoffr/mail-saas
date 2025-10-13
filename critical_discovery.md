# 🎯 CRITICAL DISCOVERY - DUAL-LANE BINNEN TIJDSLOT

## 📊 DE CRUCIALE RIJEN

### **Row 980-991: DRIE PHASES TEGELIJK (2025-10-21)**

```
Row   | Time     | Domain | Lead  | Mail | Phase
------------------------------------------------------
980   | 08:00:00 | v3     | 651   | M1   | Stream A
981   | 08:00:00 | v3     | 3     | M3   | Stream A  ← ZELFDE TIJD!
982   | 08:10:00 | v3     | 327   | M2   | Stream B
983   | 08:00:00 | v4     | 652   | M1   | Stream A
984   | 08:00:00 | v4     | 4     | M3   | Stream A  ← ZELFDE TIJD!
985   | 08:10:00 | v4     | 328   | M2   | Stream B
986   | 08:20:00 | v1     | 653   | M1   | Stream A
987   | 08:20:00 | v1     | 5     | M3   | Stream A  ← ZELFDE TIJD!
988   | 08:30:00 | v1     | 329   | M2   | Stream B
```

**PATROON:**
- v3 op 08:00: Lead 651 M1 + Lead 3 M3 (BEIDE Stream A!)
- v4 op 08:00: Lead 652 M1 + Lead 4 M3 (BEIDE Stream A!)
- v1 op 08:20: Lead 653 M1 + Lead 5 M3 (BEIDE Stream A!)

**Dit betekent:** Binnen HETZELFDE tijdslot (08:00) zijn er TWEE messages gepland voor ZELFDE domein!

---

### **Row 1310-1313: ALLE VIER PHASES! (2025-10-24)**

```
Row   | Time     | Domain | Lead  | Mail | Phase
------------------------------------------------------
1310  | 08:00:00 | v1     | 973   | M1   | Stream A
1311  | 08:00:00 | v1     | 325   | M3   | Stream A  ← ZELFDE TIJD!
1312  | 08:10:00 | v1     | 649   | M2   | Stream B
1313  | 08:10:00 | v1     | 1     | M4   | Stream B  ← ZELFDE TIJD!
```

**v1 domein op 08:00:**
- Lead 973 M1 (Stream A)
- Lead 325 M3 (Stream A)

**v1 domein op 08:10:**
- Lead 649 M2 (Stream B)
- Lead 1 M4 (Stream B)

---

## 💡 **WAT DIT BETEKENT**

### **DUAL-LANE IS NIET TUSSEN STREAMS!**

Het is: **BINNEN ZELFDE STREAM kunnen MEERDERE PHASES tegelijk due zijn!**

```
08:00 Stream A voor v1:
┌─────────────────┐
│ Lead 973 M1     │ ← Due
│ Lead 325 M3     │ ← Due
└─────────────────┘

Priority: M3 > M1
→ Verzend M3 eerst (Lane A)
→ Verzend M1 daarna (Lane B)
```

### **DE WERKELIJKE DUAL-LANE LOGICA:**

**Per 20-min venster per domein:**
1. Verzamel ALLE messages die due zijn op dit tijdslot
2. Dit kunnen messages zijn van VERSCHILLENDE mail phases:
   - M1 en M3 (beide Stream A :00/:20/:40)
   - M2 en M4 (beide Stream B :10/:30/:50)
3. Sorteer op priority: M4 > M3 > M2 > M1
4. **Verzend de top 2 (Lane A + Lane B)**

**Voorbeeld 08:00 voor v1:**
```
Due messages:
- Lead 973 M1 (priority 3)
- Lead 325 M3 (priority 1)

Sort by priority:
1. Lead 325 M3 (priority 1) → Lane A
2. Lead 973 M1 (priority 3) → Lane B

Verzend beide in dit 20-min venster!
```

---

## 🎯 **CAPACITEIT HERBEREKENING**

### **Per domein per 20-min venster: 2 messages**

**Per dag:**
```
Stream A slots: 27 (08:00-16:40, elke 20 min)
Stream B slots: 27 (08:10-16:50, elke 20 min)

Maar ze overlappen niet qua tijdstip!

Stream A op 08:00, 08:20, 08:40... (27 slots)
Stream B op 08:10, 08:30, 08:50... (27 slots)

Per slot: 2 messages kunnen verzonden worden (als beide due)
```

**Totaal per domein per dag:**
```
Als ALLEEN M1 phase actief: max 27/dag (1 per Stream A slot)
Als M1+M2 phases actief: max 54/dag (27 Stream A + 27 Stream B)
Als M1+M2+M3 actief: max 54/dag (maar nu kunnen Stream A slots 2 msgs hebben!)
Als M1+M2+M3+M4 actief: max 54/dag (Stream A kan 2, Stream B kan 2)
```

**MAAR:** Met dual-lane BINNEN slot:
```
Als op 08:00 beide M1 én M3 due zijn:
→ Verzend 2 messages in dit 20-min venster
→ Throttle geldt voor het VENSTER, niet per message

Dus per venster: max 2 messages
Per dag: 27 vensters × 2 = 54 messages/domein/dag
```

**TOTAAL CAPACITEIT:**
```
4 domeinen × 54 msgs/dag = 216 messages/dag
```

**Dit klopt met Excel:**
- 2025-10-21: 324 messages (M1+M2+M3 overlap, maar niet alle slots vol)
- Max theoretical: 216/dag als alle slots dual-lane gebruikt

---

## 🔧 **IMPLEMENTATIE CORRECTIE**

### **Priority Queue MOET werken zoals origineel beschreven!**

```python
# Voor elk domein, elk tijdslot:
def get_messages_for_slot(domain: str, slot_time: datetime) -> Tuple[Message, Message]:
    """Get Lane A and Lane B messages for a single 20-min slot."""
    
    # Get ALL messages due at this exact time for this domain
    due = [
        m for m in all_messages
        if m.domain_used == domain
        and m.scheduled_at == slot_time  # EXACT time match
        and m.status == 'queued'
    ]
    
    if not due:
        return None, None
    
    # Sort by priority (M4 > M3 > M2 > M1)
    due.sort(key=lambda m: (MAIL_PRIORITY[m.mail_number], m.lead_id))
    
    # Lane A: Highest priority
    lane_a = due[0] if len(due) >= 1 else None
    
    # Lane B: Second highest priority (or M1 if preferred)
    lane_b = None
    if len(due) >= 2:
        # Check if M1 exists in remaining
        m1_candidates = [m for m in due[1:] if m.mail_number == 1]
        if m1_candidates:
            lane_b = m1_candidates[0]
        else:
            lane_b = due[1]
    
    return lane_a, lane_b
```

### **Slot Processing:**

```python
# Worker runs every minute
current_slot = snap_to_current_slot(now)  # Round to nearest :00/:10/:20/:30/:40/:50

for domain in DOMAINS:
    lane_a, lane_b = get_messages_for_slot(domain, current_slot)
    
    if lane_a:
        send_email(lane_a)
        mark_sent(lane_a)
    
    if lane_b:
        send_email(lane_b)
        mark_sent(lane_b)
    
    # Now wait until NEXT slot (10 min later for next stream)
    # No need to throttle further - we're already on slot boundaries
```

---

## ✅ **VERIFICATION FROM EXCEL**

### **Row 1310-1313 bewijst dit:**

```
08:00 slot voor v1:
- M1 lead 973 (scheduled_at = 2025-10-24 08:00)
- M3 lead 325 (scheduled_at = 2025-10-24 08:00)

Worker op 08:00:
→ Lane A = M3 lead 325 (higher priority)
→ Lane B = M1 lead 973 (lower priority)
→ Verzend beide
→ Wacht tot 08:10

08:10 slot voor v1:
- M2 lead 649 (scheduled_at = 2025-10-24 08:10)
- M4 lead 1 (scheduled_at = 2025-10-24 08:10)

Worker op 08:10:
→ Lane A = M4 lead 1 (higher priority)
→ Lane B = M2 lead 649 (lower priority)
→ Verzend beide
→ Wacht tot 08:20
```

**In 20 minuten (08:00-08:20) heeft v1 domein 4 messages verzonden!**

Maar dat klopt niet met "1 per 20 min throttle"...

**OF:** De throttle is 10 minuten tussen streams?
- Stream A op 08:00
- Stream B op 08:10
- Verschil = 10 min

Maar binnen ZELFDE stream slot kunnen 2 messages?

---

## 🤔 **RESTERENDE VRAAG**

Hoe past de "20 min throttle" hierbij?

**Optie 1:** Throttle is per STREAM
- Stream A: 1 message per 20 min (08:00, 08:20, 08:40)
- Stream B: 1 message per 20 min (08:10, 08:30, 08:50)
- Binnen stream: Als 2 due, verzend beide direct

**Optie 2:** Throttle is globaal per domein
- Max 2 messages per 20-min window
- 1 van Stream A + 1 van Stream B
- Maar streams zijn 10 min offset, dus praktisch geen throttle issue

**Optie 3:** GEEN throttle binnen slot
- Alle messages op EXACT dezelfde scheduled_at worden samen verzonden
- Throttle geldt alleen tussen verschillende tijdslots

Welke is correct? 🎯
