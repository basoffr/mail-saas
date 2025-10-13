import pandas as pd

# Load Excel
df = pd.read_excel('Concept planning campagne.xlsx')
df = df.dropna(subset=['Lead'])

print("=" * 80)
print("EXCEL STRUCTURE ANALYSIS")
print("=" * 80)

# 1. Unique times
print("\n1. UNIQUE TIMES (first 30):")
times = df['Tijd'].unique()
for i, t in enumerate(times[:30]):
    print(f"  {i+1}. {t}")

# 2. Lead-Domain mapping
print("\n2. LEAD-DOMAIN MAPPING (leads 1-20):")
for i in range(1, 21):
    lead_data = df[df['Lead'] == i]
    if len(lead_data) > 0:
        domain = lead_data['Domein'].iloc[0]
        print(f"  Lead {i:3d}: {domain}")

# 3. Check modulo 4 pattern
print("\n3. MODULO 4 PATTERN CHECK:")
domains_map = {'v1': 0, 'v2': 1, 'v3': 2, 'v4': 3}
errors = 0
for i in range(1, 201):
    lead_data = df[df['Lead'] == i]
    if len(lead_data) > 0:
        domain = lead_data['Domein'].iloc[0]
        expected_idx = (i - 1) % 4
        expected_domain = ['v1', 'v2', 'v3', 'v4'][expected_idx]
        if domain != expected_domain:
            print(f"  [ERROR] Lead {i}: expected {expected_domain}, got {domain}")
            errors += 1

if errors == 0:
    print("  [OK] All leads follow (lead_index - 1) % 4 pattern!")
else:
    print(f"  [WARN] {errors} mismatches found")

# 4. M2 times (check Stream B)
print("\n4. M2 TIMES (first 15 - checking Stream B :10/:30/:50):")
m2 = df[df['Mail'] == 'M2'].head(15)
print(m2[['Tijd', 'Domein', 'Lead', 'Mail', 'Datum']].to_string(index=False))

# 5. Check overlapping
print("\n5. OVERLAPPING CHECK (same date, different mails):")
dates = df['Datum'].unique()
for date in dates[:3]:  # First 3 dates
    date_data = df[df['Datum'] == date]
    mail_counts = date_data['Mail'].value_counts()
    print(f"  {date}: {dict(mail_counts)}")

# 6. Slot distribution
print("\n6. MESSAGES PER SLOT (first 10 slots):")
df['Slot'] = df['Datum'].astype(str) + ' ' + df['Tijd'].astype(str)
slot_counts = df['Slot'].value_counts().head(10)
for slot, count in slot_counts.items():
    print(f"  {slot}: {count} messages")

# 7. Stream detection
print("\n7. STREAM DETECTION:")
m1_times = df[df['Mail'] == 'M1']['Tijd'].unique()[:10]
m2_times = df[df['Mail'] == 'M2']['Tijd'].unique()[:10]
print(f"  M1 times (Stream A): {[str(t) for t in m1_times]}")
print(f"  M2 times (Stream B): {[str(t) for t in m2_times]}")

# 8. Summary stats
print("\n8. SUMMARY STATS:")
print(f"  Total messages: {len(df)}")
print(f"  Unique leads: {df['Lead'].nunique()}")
print(f"  Messages per mail:")
for mail in ['M1', 'M2', 'M3', 'M4']:
    count = len(df[df['Mail'] == mail])
    print(f"    {mail}: {count}")
print(f"  Messages per domain:")
for domain in ['v1', 'v2', 'v3', 'v4']:
    count = len(df[df['Domein'] == domain])
    print(f"    {domain}: {count}")
