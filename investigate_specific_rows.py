import json

# Load JSON
with open('campaign_schedule_excel.json', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("INVESTIGATING SPECIFIC ROW RANGES")
print("="*80)

# Excel row to JSON index: Excel row 2 = JSON index 0 (first data row after header)
row_ranges = [
    (2, 4, "First messages"),
    (111, 114, "Around slot boundary?"),
    (220, 223, "Another boundary?"),
    (329, 332, "Note: User wrote 326 but likely meant 332"),
    (546, 553, "Mid-range check"),
    (763, 770, "Another check"),
    (980, 991, "Larger range"),
    (1305, 1316, "Transition point?"),
    (1630, 1641, "Another transition"),
    (1955, 1970, "Late in campaign")
]

for start_row, end_row, description in row_ranges:
    print(f"\n{'='*80}")
    print(f"ROWS {start_row}-{end_row}: {description}")
    print(f"{'='*80}")
    print(f"{'Row':<5} | {'Time':<8} | {'Domain':<6} | {'Lead':<5} | {'Mail':<4} | {'From':<25} | {'Date'}")
    print("-" * 100)
    
    # Convert Excel row to JSON index (row 2 = index 0, row 3 = index 1, etc.)
    start_idx = start_row - 2
    end_idx = end_row - 2 + 1  # +1 because range is inclusive
    
    for i in range(start_idx, min(end_idx, len(data))):
        row_num = i + 2  # Convert back to Excel row number
        msg = data[i]
        lead = int(msg['lead']) if msg['lead'] else 0
        print(f"{row_num:<5} | {msg['tijd']:<8} | {msg['domein']:<6} | {lead:<5} | {msg['mail']:<4} | {msg['from']:<25} | {msg['datum']}")

# Detailed analysis of patterns
print("\n" + "="*80)
print("PATTERN ANALYSIS")
print("="*80)

def analyze_range(start_row, end_row, label):
    start_idx = start_row - 2
    end_idx = end_row - 2 + 1
    
    msgs = data[start_idx:min(end_idx, len(data))]
    if not msgs:
        return
    
    print(f"\n{label} (Rows {start_row}-{end_row}):")
    
    # Group by unique characteristics
    times = set(m['tijd'] for m in msgs)
    mails = set(m['mail'] for m in msgs)
    dates = set(m['datum'] for m in msgs)
    domains = [m['domein'] for m in msgs]
    
    print(f"  Times: {sorted(times)}")
    print(f"  Mails: {sorted(mails)}")
    print(f"  Dates: {sorted(dates)}")
    print(f"  Domains: {domains}")
    
    # Check for transitions
    if len(times) > 1:
        print(f"  >>> TIME TRANSITION: {sorted(times)}")
    if len(mails) > 1:
        print(f"  >>> MAIL PHASE TRANSITION: {sorted(mails)}")
    if len(dates) > 1:
        print(f"  >>> DATE TRANSITION: {sorted(dates)}")

for start_row, end_row, description in row_ranges:
    analyze_range(start_row, end_row, description)

# Special focus: Look for slot boundaries
print("\n" + "="*80)
print("CRITICAL INSIGHT: WHAT ARE THESE BOUNDARIES?")
print("="*80)

print("""
Let me check if these are:
1. Time slot transitions (08:00 -> 08:10 -> 08:20)
2. Date transitions (day change)
3. Mail phase transitions (M1 -> M2)
4. Complete cycle points (all 4 domains processed)
""")

# Check row 111-114 specifically
print("\nRow 111-114 detailed:")
for i in range(109, 113):
    if i < len(data):
        msg = data[i]
        lead = int(msg['lead']) if msg['lead'] else 0
        
        # Check if this is a multiple of 4 (complete domain cycle)
        row_in_day = (i % 108) + 1  # 108 messages per day for M1 phase
        
        print(f"  Row {i+2}: {msg['datum']} {msg['tijd']} | {msg['domein']} Lead {lead:4d} {msg['mail']} | Row-in-day: {row_in_day}")

# Check for 108-message cycles (27 slots × 4 domains)
print("\n" + "="*80)
print("108-MESSAGE CYCLE ANALYSIS (27 slots × 4 domains)")
print("="*80)

cycle_points = [109, 217, 325, 433, 541, 649, 757, 865, 973, 1081, 1189, 1297]
print("\nMessages at every 108th position:")
print(f"{'Index':<6} | {'Row':<5} | {'Time':<8} | {'Domain':<6} | {'Lead':<5} | {'Mail':<4} | {'Date'}")
print("-" * 80)

for idx in cycle_points:
    if idx < len(data):
        msg = data[idx]
        row_num = idx + 2
        lead = int(msg['lead']) if msg['lead'] else 0
        print(f"{idx:<6} | {row_num:<5} | {msg['tijd']:<8} | {msg['domein']:<6} | {lead:<5} | {msg['mail']:<4} | {msg['datum']}")

print("\n" + "="*80)
print("HYPOTHESIS: These rows mark SLOT or PHASE boundaries")
print("="*80)
