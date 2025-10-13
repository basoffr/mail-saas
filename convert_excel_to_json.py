import pandas as pd
import json
from datetime import datetime

# Load Excel
df = pd.read_excel('Concept planning campagne.xlsx')

# Drop NaN rows
df = df.dropna(subset=['Lead'])

# Convert to records
records = []
for idx, row in df.iterrows():
    record = {
        'tijd': str(row['Tijd']) if pd.notna(row['Tijd']) else None,
        'domein': row['Domein'] if pd.notna(row['Domein']) else None,
        'lead': int(row['Lead']) if pd.notna(row['Lead']) else None,
        'mail': row['Mail'] if pd.notna(row['Mail']) else None,
        'from': row['From'] if pd.notna(row['From']) else None,
        'datum': row['Datum'].strftime('%Y-%m-%d') if pd.notna(row['Datum']) else None,
    }
    records.append(record)

# Save to JSON
with open('campaign_schedule_excel.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"Converted {len(records)} records to JSON")

# Analysis
print("\n" + "="*80)
print("DETAILED ANALYSIS")
print("="*80)

# Group by lead
leads_data = {}
for rec in records:
    lead = rec['lead']
    if lead not in leads_data:
        leads_data[lead] = []
    leads_data[lead].append(rec)

# Analyze first 10 leads in detail
print("\nFIRST 10 LEADS - FULL DETAIL:")
for lead in sorted(leads_data.keys())[:10]:
    mails = leads_data[lead]
    print(f"\n--- LEAD {lead} ({mails[0]['domein']}) ---")
    for mail in mails:
        print(f"  {mail['mail']:3s} | {mail['datum']} {mail['tijd']} | {mail['from']}")

# Check stream pattern
print("\n" + "="*80)
print("STREAM PATTERN VERIFICATION")
print("="*80)

stream_a_minutes = set()
stream_b_minutes = set()

for rec in records:
    if rec['mail'] in ['M1', 'M3']:
        time_str = rec['tijd']
        minute = int(time_str.split(':')[1]) if time_str else None
        if minute is not None:
            stream_a_minutes.add(minute)
    elif rec['mail'] in ['M2', 'M4']:
        time_str = rec['tijd']
        minute = int(time_str.split(':')[1]) if time_str else None
        if minute is not None:
            stream_b_minutes.add(minute)

print(f"Stream A (M1/M3) minutes: {sorted(stream_a_minutes)}")
print(f"Stream B (M2/M4) minutes: {sorted(stream_b_minutes)}")

# Check workday offsets
print("\n" + "="*80)
print("WORKDAY OFFSET VERIFICATION")
print("="*80)

for lead in [1, 2, 3, 4, 5]:
    if lead in leads_data:
        mails = leads_data[lead]
        print(f"\nLead {lead} ({mails[0]['domein']}):")
        
        m1_date = None
        for mail in mails:
            if mail['mail'] == 'M1':
                m1_date = datetime.strptime(mail['datum'], '%Y-%m-%d')
                print(f"  M1: {mail['datum']} {mail['tijd']}")
                break
        
        if m1_date:
            for mail in mails:
                if mail['mail'] in ['M2', 'M3', 'M4']:
                    mail_date = datetime.strptime(mail['datum'], '%Y-%m-%d')
                    delta = (mail_date - m1_date).days
                    
                    # Count workdays
                    workdays = 0
                    current = m1_date
                    while current < mail_date:
                        current = current.replace(hour=0, minute=0, second=0, microsecond=0) + pd.Timedelta(days=1)
                        if current.weekday() < 5:  # Mon-Fri
                            workdays += 1
                    
                    print(f"  {mail['mail']}: {mail['datum']} {mail['tijd']} (+{delta} cal days, +{workdays} workdays)")

# Domain distribution
print("\n" + "="*80)
print("DOMAIN DISTRIBUTION")
print("="*80)

domain_counts = {}
for lead, mails in leads_data.items():
    domain = mails[0]['domein']
    if domain not in domain_counts:
        domain_counts[domain] = []
    domain_counts[domain].append(lead)

for domain in sorted(domain_counts.keys()):
    leads = domain_counts[domain]
    print(f"{domain}: {len(leads)} leads")
    print(f"  Lead range: {min(leads)}-{max(leads)}")
    print(f"  Sample leads: {sorted(leads)[:10]}")

# Overlapping check
print("\n" + "="*80)
print("OVERLAPPING PHASES (same date)")
print("="*80)

dates_analysis = {}
for rec in records:
    date = rec['datum']
    if date not in dates_analysis:
        dates_analysis[date] = {'M1': 0, 'M2': 0, 'M3': 0, 'M4': 0}
    if rec['mail'] in dates_analysis[date]:
        dates_analysis[date][rec['mail']] += 1

print("\nDate         | M1  | M2  | M3  | M4  | Total")
print("-" * 60)
for date in sorted(dates_analysis.keys())[:15]:  # First 15 days
    counts = dates_analysis[date]
    total = sum(counts.values())
    print(f"{date} | {counts['M1']:3d} | {counts['M2']:3d} | {counts['M3']:3d} | {counts['M4']:3d} | {total:3d}")

# Dual-lane per slot
print("\n" + "="*80)
print("DUAL-LANE VERIFICATION (messages per timeslot)")
print("="*80)

slot_analysis = {}
for rec in records:
    slot_key = f"{rec['datum']} {rec['tijd']}"
    if slot_key not in slot_analysis:
        slot_analysis[slot_key] = []
    slot_analysis[slot_key].append(rec)

print("\nTimeslot           | Msgs | Domains    | Mails")
print("-" * 70)
for slot in sorted(slot_analysis.keys())[:20]:  # First 20 slots
    msgs = slot_analysis[slot]
    domains = [m['domein'] for m in msgs]
    mails = [m['mail'] for m in msgs]
    print(f"{slot} | {len(msgs):4d} | {','.join(set(domains)):10s} | {','.join(set(mails))}")

print("\n" + "="*80)
print(f"JSON saved to: campaign_schedule_excel.json")
print("="*80)
