import json
from collections import defaultdict

with open('campaign_schedule_excel.json', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("PHASE OVERLAP ANALYSIS - MESSAGES PER 20-MIN WINDOW")
print("="*80)

# Group by date and 20-min window
windows = defaultdict(list)

for msg in data:
    date = msg['datum']
    time = msg['tijd']
    
    # Extract hour and minute
    hour = int(time.split(':')[0])
    minute = int(time.split(':')[1])
    
    # Group into 20-min windows (08:00-08:20, 08:20-08:40, etc)
    # Round down to nearest 20-min mark
    window_minute = (minute // 20) * 20
    window_key = f"{date} {hour:02d}:{window_minute:02d}"
    
    windows[window_key].append(msg)

# Analyze first few days
print("\nFIRST 15 DAYS - Messages per 20-min window (08:00-08:20 slot):")
print("Date       | Window   | Count | Mail Phases Present")
print("-"*80)

dates = sorted(set(msg['datum'] for msg in data))
for date in dates[:15]:
    window_key = f"{date} 08:00"
    if window_key in windows:
        msgs = windows[window_key]
        count = len(msgs)
        
        # What phases are present?
        phases = set(m['mail'] for m in msgs)
        phases_str = ','.join(sorted(phases))
        
        print(f"{date} | 08:00-20 | {count:5d} | {phases_str}")

# Detailed breakdown of specific days
print("\n" + "="*80)
print("DETAILED BREAKDOWN - WHY 4, 8, 12, 16?")
print("="*80)

key_dates = [
    ('2025-10-13', 'Day 1: M1 only'),
    ('2025-10-14', 'Day 2: M1 only'),
    ('2025-10-15', 'Day 3: M1 only'),
    ('2025-10-16', 'Day 4: M1+M2 start'),
    ('2025-10-21', 'Day 9: M1+M2+M3'),
    ('2025-10-24', 'Day 12: M1+M2+M3+M4'),
]

for date, label in key_dates:
    print(f"\n{label} ({date}):")
    print("  Time     | Domain | Lead | Mail | Alias")
    print("  " + "-"*60)
    
    # Get messages in 08:00-08:20 window
    msgs_08_00 = [m for m in data if m['datum'] == date and m['tijd'] == '08:00:00']
    msgs_08_10 = [m for m in data if m['datum'] == date and m['tijd'] == '08:10:00']
    
    all_msgs = sorted(msgs_08_00 + msgs_08_10, key=lambda m: m['tijd'])
    
    for msg in all_msgs[:20]:  # First 20
        lead = int(msg['lead']) if msg['lead'] else 0
        alias = 'chr' if 'christian' in msg['from'] else 'vic'
        print(f"  {msg['tijd']} | {msg['domein']:6s} | {lead:4d} | {msg['mail']:4s} | {alias}")
    
    print(f"\n  08:00 slot: {len(msgs_08_00)} messages")
    print(f"  08:10 slot: {len(msgs_08_10)} messages")
    print(f"  20-min window total: {len(msgs_08_00) + len(msgs_08_10)}")

# Explain the pattern
print("\n" + "="*80)
print("THE PATTERN EXPLAINED")
print("="*80)
print("""
20-MIN WINDOW = 2 tijdslots (Stream A + Stream B)

Example: 08:00-08:20 window bevat:
  - 08:00 slot (Stream A: M1, M3)
  - 08:10 slot (Stream B: M2, M4)

DAG 1-3 (M1 only):
  08:00 slot: 4 domains × 1 mail (M1 chr) = 4
  08:10 slot: 0 (geen M2 nog)
  Window total: 4 messages

DAG 4+ (M1 + M2):
  08:00 slot: 4 domains × 1 mail (M1 chr) = 4
  08:10 slot: 4 domains × 1 mail (M2 chr) = 4
  Window total: 8 messages

DAG 9+ (M1 + M2 + M3):
  08:00 slot: 4 domains × 2 mails (M1 chr + M3 vic) = 8
  08:10 slot: 4 domains × 1 mail (M2 chr) = 4
  Window total: 12 messages

DAG 12+ (M1 + M2 + M3 + M4):
  08:00 slot: 4 domains × 2 mails (M1 chr + M3 vic) = 8
  08:10 slot: 4 domains × 2 mails (M2 chr + M4 vic) = 8
  Window total: 16 messages

END PHASE (winding down):
  - Nieuwe leads stoppen (no more M1)
  - Oude leads replies/unsub (M2-M4 canceled)
  - 16 → 12 → 8 → 4 → 0
""")

# Check the wind-down
print("\n" + "="*80)
print("WIND-DOWN PHASE (last days)")
print("="*80)

last_dates = dates[-5:]
print("\nDate       | 08:00 slot | 08:10 slot | Window total")
print("-"*70)

for date in last_dates:
    msgs_08_00 = [m for m in data if m['datum'] == date and m['tijd'] == '08:00:00']
    msgs_08_10 = [m for m in data if m['datum'] == date and m['tijd'] == '08:10:00']
    
    print(f"{date} | {len(msgs_08_00):10d} | {len(msgs_08_10):10d} | {len(msgs_08_00) + len(msgs_08_10):12d}")
