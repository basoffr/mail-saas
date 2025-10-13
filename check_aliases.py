import json

with open('campaign_schedule_excel.json', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("ALIAS DISCOVERY - THE MISSING PIECE!")
print("="*80)

# Check row 1310-1313
print("\nRow 1310-1313 WITH ALIASES:")
print("Row  | Time     | Domain | Lead | Mail | FROM ALIAS")
print("-"*80)
for i in range(1308, 1313):
    msg = data[i]
    lead = int(msg['lead'])
    print(f"{i+2:4d} | {msg['tijd']} | {msg['domein']:6s} | {lead:4d} | {msg['mail']:4s} | {msg['from']}")

# Check row 980-991
print("\n" + "="*80)
print("Row 980-991 WITH ALIASES:")
print("Row  | Time     | Domain | Lead | Mail | FROM ALIAS")
print("-"*80)
for i in range(978, 992):
    msg = data[i]
    lead = int(msg['lead'])
    print(f"{i+2:4d} | {msg['tijd']} | {msg['domein']:6s} | {lead:4d} | {msg['mail']:4s} | {msg['from']}")

# Analyze alias pattern
print("\n" + "="*80)
print("ALIAS PATTERN ANALYSIS")
print("="*80)

alias_by_mail = {1: set(), 2: set(), 3: set(), 4: set()}
for msg in data[:100]:
    mail_num = msg['mail']
    if mail_num in ['M1', 'M2', 'M3', 'M4']:
        mail_num = int(mail_num[1])
        from_field = msg['from']
        
        # Extract alias (christian or victor)
        if 'christian' in from_field:
            alias_by_mail[mail_num].add('christian')
        elif 'victor' in from_field:
            alias_by_mail[mail_num].add('victor')

print("\nAlias mapping per mail number:")
for mail_num in sorted(alias_by_mail.keys()):
    aliases = alias_by_mail[mail_num]
    print(f"  M{mail_num}: {', '.join(sorted(aliases))}")

# Check slots with 2 messages same domain
print("\n" + "="*80)
print("SLOTS WITH 2+ MESSAGES SAME DOMAIN (First 10 examples)")
print("="*80)

slot_analysis = {}
for msg in data:
    key = f"{msg['datum']} {msg['tijd']} {msg['domein']}"
    if key not in slot_analysis:
        slot_analysis[key] = []
    slot_analysis[key].append(msg)

# Find slots with 2+ messages
multi_msg_slots = {k: v for k, v in slot_analysis.items() if len(v) >= 2}

print(f"\nTotal slots with 2+ messages: {len(multi_msg_slots)}")
print("\nFirst 10 examples:")
print("Date       | Time     | Domain | Count | Messages")
print("-"*80)

for i, (slot_key, msgs) in enumerate(sorted(multi_msg_slots.items())[:10]):
    date, time, domain = slot_key.split()
    
    msg_summary = []
    for msg in msgs:
        lead = int(msg['lead'])
        alias = 'chr' if 'christian' in msg['from'] else 'vic'
        msg_summary.append(f"{msg['mail']}({alias},{lead})")
    
    print(f"{date} | {time} | {domain:6s} | {len(msgs):5d} | {', '.join(msg_summary)}")

# Detailed analysis of ONE slot
print("\n" + "="*80)
print("DETAILED: 2025-10-24 08:00 v1 (4 messages!)")
print("="*80)

target_msgs = [m for m in data if m['datum'] == '2025-10-24' and m['tijd'] == '08:00:00' and m['domein'] == 'v1']
print("Lead | Mail | Alias      | Full FROM")
print("-"*60)
for msg in target_msgs:
    lead = int(msg['lead'])
    alias = 'christian' if 'christian' in msg['from'] else 'victor'
    print(f"{lead:4d} | {msg['mail']:4s} | {alias:10s} | {msg['from']}")

print("\n" + "="*80)
print("THE PATTERN:")
print("="*80)
print("""
DUAL-LANE = DUAL ALIAS per domein!

Per 20-min slot per domein kunnen TWEE messages verzonden:
  Lane A (christian@): M1 of M2 messages
  Lane B (victor@):    M3 of M4 messages

Dit werkt omdat:
- M1/M2 gebruiken christian@ als FROM
- M3/M4 gebruiken victor@ als FROM
- SMTP kan parallelliseren op FROM address
- Verschillende FROM = verschillende "sender lanes"

Stream A/B (tijdslots) CROSSED MET alias lanes:
  08:00 Stream A: christian@ (M1) + victor@ (M3) = 2 messages
  08:10 Stream B: christian@ (M2) + victor@ (M4) = 2 messages
  08:20 Stream A: christian@ (M1) + victor@ (M3) = 2 messages
  ...

Capaciteit:
  Per slot: 2 messages (1 christian + 1 victor)
  Per dag: 54 slots × 2 aliases = 54 messages/domein
  
MAAR: Alleen als BEIDE aliases messages hebben die due zijn!
""")
