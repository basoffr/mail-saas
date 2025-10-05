# -*- coding: utf-8 -*-
"""
IMPORT REMAINING LEADS - Robust One-by-One Import
Import missing 850+ leads that failed in batch import
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
from tqdm import tqdm

# Configuration
SUPABASE_URL = "https://zpnklihryhpkaiyubkfn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDMzNDIsImV4cCI6MjA3NDcxOTM0Mn0.P8Rx3r--uu8V-HCEH2s5qH3Ud0HhpLBUWaidrahO0jY"

BASE_DIR = Path(__file__).parent
EXCEL_FILE = BASE_DIR / "Importable data" / "leads_transformed_v2.xlsx"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_id(prefix: str, unique_string: str) -> str:
    hash_suffix = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    return f"{prefix}_{hash_suffix}"

def extract_domain(url: str) -> str:
    if not url:
        return None
    domain = url.replace("https://", "").replace("http://", "")
    domain = domain.replace("www.", "")
    domain = domain.split("/")[0]
    domain = domain.split(":")[0]
    return domain

def main():
    print("="*70)
    print("🔄 IMPORT REMAINING LEADS")
    print("="*70)
    
    # Read Excel and deduplicate
    df = pd.read_excel(EXCEL_FILE)
    print(f"\n📊 Excel: {len(df)} total rows")
    
    # Keep first occurrence of duplicate emails
    df_unique = df.drop_duplicates(subset=['email'], keep='first')
    print(f"📊 After deduplication: {len(df_unique)} unique emails")
    
    # Get existing leads
    existing_result = supabase.table("leads").select("email").execute()
    existing_emails = {r['email'] for r in existing_result.data}
    print(f"📊 Already in database: {len(existing_emails)} leads")
    
    # Filter to only missing leads
    df_missing = df_unique[~df_unique['email'].isin(existing_emails)]
    print(f"📊 To import: {len(df_missing)} missing leads")
    
    if len(df_missing) == 0:
        print("\n✅ All leads already imported!")
        return
    
    # Import one by one
    print(f"\n🚀 Starting import...")
    success = 0
    failed = 0
    failed_emails = []
    
    for _, row in tqdm(df_missing.iterrows(), total=len(df_missing), desc="Importing"):
        email = row['email']
        url = row.get('url', '')
        company = row.get('company', '')
        
        try:
            lead_id = generate_id("lead", email)
            domain = extract_domain(url) if url else None
            
            vars_data = {
                "keyword": str(row.get('keyword', '')),
                "google_rank": str(row.get('google_rank', '')),
                "seo_score": str(row.get('seo_score', ''))
            }
            
            lead = {
                "id": lead_id,
                "email": email,
                "company": company or None,
                "url": url or None,
                "domain": domain,
                "status": "active",
                "vars": json.dumps(vars_data),
                "tags": json.dumps([]),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("leads").insert(lead).execute()
            success += 1
            
        except Exception as e:
            failed += 1
            failed_emails.append((email, str(e)[:50]))
            if failed <= 5:  # Show first 5 errors
                tqdm.write(f"⚠️  Failed: {email[:40]} - {str(e)[:60]}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 IMPORT COMPLETE")
    print("="*70)
    print(f"✅ Successfully imported: {success}")
    print(f"⚠️  Failed: {failed}")
    
    if failed > 0 and failed <= 20:
        print(f"\n❌ Failed emails:")
        for email, error in failed_emails[:20]:
            print(f"   - {email[:50]}: {error}")
    
    # Final database count
    final_result = supabase.table("leads").select("id", count='exact').execute()
    print(f"\n📊 Total leads in database: {final_result.count}")
    print("="*70)

if __name__ == "__main__":
    main()
