#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix SQL syntax - add ::text casting for Postgres compatibility.
"""

import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

workspace_root = Path(__file__).parent.parent
input_file = workspace_root / "scripts" / "fix_report_filenames_combined.sql"
output_file = workspace_root / "scripts" / "fix_report_filenames_CORRECTED.sql"

print("📂 Reading SQL file...")
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("🔧 Fixing syntax...")
# Replace all to_jsonb('filename')) with to_jsonb('filename'::text))
import re
corrected = re.sub(
    r"to_jsonb\('([^']+)'\)\)",
    r"to_jsonb('\1'::text))",
    content
)

print("💾 Writing corrected file...")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(corrected)

print(f"\n✅ Corrected SQL file created: {output_file}")
print("\n📋 INSTRUCTIONS:")
print("1. Open Supabase SQL Editor: https://supabase.com/dashboard")
print("2. Copy ENTIRE content of fix_report_filenames_CORRECTED.sql")
print("3. Paste into SQL Editor")
print("4. Click 'Run' - updates 1067 leads in one transaction")
print("5. Verify: SELECT COUNT(*) FROM leads WHERE vars->>'report_filename' LIKE '%_com_%' OR vars->>'report_filename' LIKE '%_nl_%';")
