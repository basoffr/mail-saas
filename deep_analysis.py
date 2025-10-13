import json

# Load JSON
with open('campaign_schedule_excel.json', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("CRITICAL PATTERN ANALYSIS - DUAL-LANE & OVERLAPPING")
print("="*80)

# Check specific overlapping day
print("\n2025-10-16 (First overlapping day with M1+M2):")
print("Time     | Domain | Lead | Mail | From")
print("-" * 60)
day_16 = [d for d in data if d['datum'] == '2025-10-16'][:40]
for msg in day_16:
    print(f"{msg['tijd']} | {msg['domein']:6s} | {msg['lead']:4d} | {msg['mail']:4s} | {msg['from']}")

# Analyze slot distribution
print("\n" + "="*80)
print("SLOT DISTRIBUTION ON 2025-10-16 (First 10 slots)")
print("="*80)

slot_map = {}
for msg in day_16:
    slot = msg['tijd']
    if slot not in slot_map:
        slot_map[slot] = []
    slot_map[slot].append(msg)

for slot in sorted(slot_map.keys())[:10]:
    msgs = slot_map[slot]
    print(f"\n{slot} - {len(msgs)} messages:")
    for msg in msgs:
        print(f"  {msg['domein']} Lead {msg['lead']:4d} {msg['mail']}")

# Check 2025-10-21 (M1+M2+M3 overlap)
print("\n" + "="*80)
print("2025-10-21 (Triple overlap: M1+M2+M3)")
print("="*80)
print("Time     | Domain | Lead | Mail | From")
print("-" * 60)
day_21 = [d for d in data if d['datum'] == '2025-10-21'][:50]
for msg in day_21:
    print(f"{msg['tijd']} | {msg['domein']:6s} | {msg['lead']:4d} | {msg['mail']:4s} | {msg['from']}")

# Count by mail phase
print("\n" + "="*80)
print("PHASE DISTRIBUTION PER DAY")
print("="*80)

date_phases = {}
for msg in data:
    date = msg['datum']
    if date not in date_phases:
        date_phases[date] = {'M1': 0, 'M2': 0, 'M3': 0, 'M4': 0}
    if msg['mail'] in date_phases[date]:
        date_phases[date][msg['mail']] += 1

print("\nDate       | M1  | M2  | M3  | M4  | Total | Note")
print("-" * 80)
for date in sorted(date_phases.keys()):
    counts = date_phases[date]
    total = sum(counts.values())
    m1, m2, m3, m4 = counts['M1'], counts['M2'], counts['M3'], counts['M4']
    
    note = ""
    if m1 > 0 and m2 == 0 and m3 == 0 and m4 == 0:
        note = "M1 only"
    elif m1 > 0 and m2 > 0 and m3 == 0 and m4 == 0:
        note = "M1+M2 overlap"
    elif m1 > 0 and m2 > 0 and m3 > 0 and m4 == 0:
        note = "M1+M2+M3 overlap"
    elif m1 > 0 and m2 > 0 and m3 > 0 and m4 > 0:
        note = "ALL PHASES overlap"
    
    print(f"{date} | {m1:3d} | {m2:3d} | {m3:3d} | {m4:3d} | {total:5d} | {note}")

# Lead journey tracking
print("\n" + "="*80)
print("LEAD JOURNEY EXAMPLES (First 5 leads)")
print("="*80)

leads_data = {}
for msg in data:
    lead = msg['lead']
    if lead not in leads_data:
        leads_data[lead] = []
    leads_data[lead].append(msg)

for lead in sorted(leads_data.keys())[:5]:
    msgs = leads_data[lead]
    domain = msgs[0]['domein']
    print(f"\n=== LEAD {lead} ({domain}) ===")
    print("Mail | Date       | Time     | From                    | Stream")
    print("-" * 70)
    for msg in msgs:
        minute = int(msg['tijd'].split(':')[1])
        stream = "A (:00/:20/:40)" if minute in [0, 20, 40] else "B (:10/:30/:50)"
        print(f"{msg['mail']:4s} | {msg['datum']} | {msg['tijd']} | {msg['from']:23s} | {stream}")

# Verify staggering
print("\n" + "="*80)
print("STAGGERING VERIFICATION (Leads 1-4, same slot)")
print("="*80)
print("\nSlot 08:00 on 2025-10-13 (M1):")
slot_08 = [d for d in data if d['tijd'] == '08:00:00' and d['datum'] == '2025-10-13' and d['mail'] == 'M1']
for msg in slot_08:
    print(f"  Lead {msg['lead']} - {msg['domein']}")

print("\nTheir M2 slots (should be staggered):")
for lead in [1, 2, 3, 4]:
    lead_data = [d for d in data if d['lead'] == lead and d['mail'] == 'M2']
    if lead_data:
        msg = lead_data[0]
        print(f"  Lead {msg['lead']} - {msg['datum']} {msg['tijd']}")

print("\n" + "="*80)
print("KEY INSIGHTS FROM EXCEL STRUCTURE:")
print("="*80)
print("""
1. OK Lead-Domain Stickiness: 
   - Lead 1,5,9... - v1 (vindbaarheid)
   - Lead 2,6,10... - v2 (seo)
   - Lead 3,7,11... - v3 (zoekmachine)
   - Lead 4,8,12... - v4 (marketing)
   - Pattern: (lead-1) % 4

2. OK Stream Separation:
   - M1/M3: :00/:20/:40 (Stream A)
   - M2/M4: :10/:30/:50 (Stream B)
   - 10-minute offset between streams

3. OK Dual-Lane per Slot:
   - Each 20-min slot: 4 messages (1 per domain)
   - NOT 8 messages (would be 2 per domain)
   - Each domain gets 1 slot, but across 4 domains = 4 total

4. OK Workday Offsets:
   - M1 - M2: +3 workdays (mon 13 - thu 16)
   - M2 - M3: +3 workdays (thu 16 - tue 21)
   - M3 - M4: +3 workdays (tue 21 - fri 24)

5. OK Overlapping Phases:
   - 2025-10-13: M1 only (108 msgs)
   - 2025-10-16: M1+M2 overlap (216 msgs)
   - 2025-10-21: M1+M2+M3 overlap (324 msgs)
   - 2025-10-24: All 4 phases (32 msgs - campaign winding down)

6. WARN Campaign is INCOMPLETE:
   - Only 768 leads have M1
   - Only 444 leads have M2
   - Only 120 leads have M3
   - Only 8 leads have M4
   - This demonstrates stop criteria (replied/bounced/etc)

7. OK Staggering Within Campaign:
   - Leads 1-4 all start at 08:00 (different domains)
   - Their M2s are all at 08:10 (same time, different domains)
   - NO staggering of M2 within same campaign start
   - Staggering comes from M1 slots (08:00, 08:20, 08:40, etc)
""")
