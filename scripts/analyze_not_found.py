#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep analysis of 138 "not found" leads.
Investigates WHY they don't have matching reports in Storage.
"""

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Read CSV files
workspace_root = Path(__file__).parent.parent
storage_csv = workspace_root / "Supabase Snippet List Objects in Reports Bucket.csv"
leads_csv = workspace_root / "Supabase Snippet List Leads Table.csv"
results_json = workspace_root / "scripts" / "report_matching_results.json"

# Load storage filenames
print("📂 Loading storage filenames...")
storage_files = []
with open(storage_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        storage_files.append(row['name'])

print(f"✅ Found {len(storage_files)} files in Storage")

# Load matching results
print("\n📋 Loading matching results...")
with open(results_json, 'r', encoding='utf-8') as f:
    results = json.load(f)

not_found = results['not_found']
print(f"✅ Found {len(not_found)} 'not found' leads")

# Analyze patterns
print("\n🔍 ANALYZING NOT FOUND LEADS...\n")

# Group by reason
by_reason = defaultdict(list)
for item in not_found:
    reason = item['reason']
    by_reason[reason].append(item)

print("="*80)
print(f"📊 BREAKDOWN BY REASON:")
for reason, items in by_reason.items():
    print(f"  {reason}: {len(items)} leads")
print("="*80)

# Analyze TLDs
tld_counts = defaultdict(int)
for item in not_found:
    domain = item['lead']['domain']
    if '.' in domain:
        tld = domain.split('.')[-1]
        tld_counts[tld] += 1

print(f"\n🌐 TLD DISTRIBUTION:")
for tld, count in sorted(tld_counts.items(), key=lambda x: -x[1]):
    print(f"  .{tld}: {count} leads")

# Check if these domains have screenshots
print(f"\n📸 SCREENSHOT CHECK:")
has_screenshot = 0
no_screenshot = 0
for item in not_found:
    if item['lead'].get('image_key'):
        has_screenshot += 1
    else:
        no_screenshot += 1

print(f"  Has screenshot: {has_screenshot}")
print(f"  No screenshot:  {no_screenshot}")

# Try alternative matching strategies
print(f"\n🔬 ALTERNATIVE MATCHING STRATEGIES:\n")

alternative_matches = []
still_not_found = []

for item in not_found:
    domain = item['lead']['domain']
    normalized = item['normalized']
    
    # Strategy 1: Fuzzy match on domain base (before first dot)
    base_domain = domain.split('.')[0]
    
    # Strategy 2: Try with different normalizations
    attempts = [
        base_domain,  # Just "koester-conceptstore"
        base_domain.replace('-', '_'),  # "koester_conceptstore"
        domain.replace('.', '_'),  # Full domain with underscores
        domain.replace('-', '_').replace('.', '_'),  # All to underscores
    ]
    
    found_match = False
    for attempt in attempts:
        matches = [f for f in storage_files if attempt in f and f.endswith('_report.pdf')]
        if matches:
            alternative_matches.append({
                'lead': item['lead'],
                'strategy': f"Pattern: '{attempt}'",
                'matches': matches
            })
            found_match = True
            break
    
    if not found_match:
        still_not_found.append(item)

print(f"✅ Found with alternative strategies: {len(alternative_matches)}")
print(f"❌ Still not found:                   {len(still_not_found)}")

# Show sample alternative matches
if alternative_matches:
    print(f"\n🎯 SAMPLE ALTERNATIVE MATCHES (first 10):\n")
    for i, item in enumerate(alternative_matches[:10]):
        print(f"{i+1}. Domain: {item['lead']['domain']}")
        print(f"   Strategy: {item['strategy']}")
        num_matches = len(item['matches'])
        if num_matches == 1:
            print(f"   Found: {item['matches'][0]}")
        else:
            print(f"   Found: {num_matches} candidates")
            for m in item['matches'][:3]:
                print(f"          - {m}")
        print()

# Show truly not found
if still_not_found:
    print(f"\n❌ TRULY NOT FOUND (first 20):\n")
    for i, item in enumerate(still_not_found[:20]):
        domain = item['lead']['domain']
        normalized = item['normalized']
        
        # Check if ANY file contains any part of the domain
        domain_parts = domain.replace('-', '_').replace('.', '_').split('_')
        partial_matches = []
        for part in domain_parts:
            if len(part) > 3:  # Skip very short parts
                matches = [f for f in storage_files if part.lower() in f.lower()]
                if matches:
                    partial_matches.extend(matches[:2])  # Max 2 per part
        
        print(f"{i+1}. {domain}")
        print(f"   Normalized: {normalized}")
        print(f"   Image: {'YES' if item['lead'].get('image_key') else 'NO'}")
        if partial_matches:
            print(f"   Partial matches: {len(set(partial_matches))} files")
            for pm in list(set(partial_matches))[:2]:
                print(f"     - {pm}")
        else:
            print(f"   No partial matches found")
        print()

# Export detailed analysis
analysis_file = workspace_root / "scripts" / "not_found_analysis.json"
print(f"\n💾 Exporting detailed analysis...")

analysis = {
    'summary': {
        'total_not_found': len(not_found),
        'alternative_matches': len(alternative_matches),
        'truly_not_found': len(still_not_found)
    },
    'by_tld': dict(tld_counts),
    'alternative_matches': alternative_matches,
    'still_not_found': still_not_found
}

with open(analysis_file, 'w', encoding='utf-8') as f:
    json.dump(analysis, f, indent=2, ensure_ascii=False)

print(f"✅ Analysis exported: {analysis_file}")

# Generate additional SQL for alternative matches
if alternative_matches:
    sql_file = workspace_root / "scripts" / "fix_report_filenames_alternative.sql"
    print(f"\n📝 Generating SQL for alternative matches...")
    
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write("-- SQL statements for alternative matches\n")
        f.write("-- Generated by analyze_not_found.py\n")
        f.write(f"-- Total updates: {len(alternative_matches)}\n")
        f.write("-- WARNING: Review carefully - these used fuzzy matching!\n\n")
        
        for item in alternative_matches:
            if len(item['matches']) == 1:  # Only if exactly 1 match
                lead_id = item['lead']['id']
                domain = item['lead']['domain']
                correct_filename = item['matches'][0]
                
                f.write(f"-- Domain: {domain} (Strategy: {item['strategy']})\n")
                f.write(f"UPDATE leads\n")
                f.write(f"SET vars = jsonb_set(\n")
                f.write(f"    vars,\n")
                f.write(f"    '{{report_filename}}',\n")
                f.write(f"    to_jsonb('{correct_filename}')\n")
                f.write(f")\n")
                f.write(f"WHERE id = '{lead_id}';\n\n")
    
    print(f"✅ Alternative SQL created: {sql_file}")

print("\n" + "="*80)
print("🎉 DEEP ANALYSIS COMPLETE!")
print("="*80)
print(f"\n📊 FINAL SUMMARY:")
print(f"  Original not found:        {len(not_found)}")
print(f"  Found with alternatives:   {len(alternative_matches)}")
print(f"  Truly missing from storage: {len(still_not_found)}")
print(f"\n💡 These {len(still_not_found)} leads genuinely have no report in Storage.")
print("="*80)
