# -*- coding: utf-8 -*-
"""
CREATE REPORT LINKS - Link all reports to leads
Match reports to leads based on URL domain matching
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import hashlib
from pathlib import Path
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
    return domain.lower()

def fetch_all_records(table_name: str, columns: str):
    """Fetch all records from table using pagination"""
    all_records = []
    page_size = 1000
    offset = 0
    
    while True:
        result = supabase.table(table_name).select(columns).range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        all_records.extend(result.data)
        if len(result.data) < page_size:
            break
        offset += page_size
    
    return all_records

def main():
    print("="*70)
    print("🔗 CREATE REPORT LINKS")
    print("="*70)
    
    # Get all leads with email-to-id mapping
    print("\n🔍 Loading leads from database...")
    leads_data = fetch_all_records("leads", "id,email,url")
    email_to_lead = {r['email']: {'id': r['id'], 'url': r.get('url')} for r in leads_data}
    print(f"✅ Loaded {len(email_to_lead)} leads")
    
    # Get all reports
    print("\n🔍 Loading reports from database...")
    reports_data = fetch_all_records("reports", "id,filename")
    reports = {r['filename']: r['id'] for r in reports_data}
    print(f"✅ Loaded {len(reports)} reports")
    
    # Get existing links
    print("\n🔍 Checking existing links...")
    existing_data = fetch_all_records("report_links", "lead_id,report_id")
    existing_links = {(r['lead_id'], r['report_id']) for r in existing_data}
    print(f"✅ Found {len(existing_links)} existing links")
    
    # Read Excel
    df = pd.read_excel(EXCEL_FILE)
    print(f"\n📊 Processing {len(df)} rows from Excel...")
    
    # Create links
    created = 0
    skipped = 0
    no_match = 0
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Creating links"):
        email = row['email']
        url = row.get('url', '')
        
        if not url or email not in email_to_lead:
            no_match += 1
            continue
        
        lead_id = email_to_lead[email]['id']
        domain = extract_domain(url)
        
        if not domain:
            no_match += 1
            continue
        
        # Try to find matching report
        domain_clean = domain.replace(".", "_").replace("-", "_")
        
        matched_report_id = None
        for filename, report_id in reports.items():
            filename_clean = filename.lower().replace(".pdf", "").replace("-", "_")
            
            # Try multiple matching strategies
            if (domain_clean in filename_clean or 
                domain.replace(".", "_") in filename_clean or
                domain.replace("-", "_") in filename_clean):
                matched_report_id = report_id
                break
        
        if not matched_report_id:
            no_match += 1
            continue
        
        # Check if link already exists
        if (lead_id, matched_report_id) in existing_links:
            skipped += 1
            continue
        
        # Create link
        try:
            from datetime import datetime
            link_id = generate_id("link", f"{matched_report_id}_{lead_id}")
            link = {
                "id": link_id,
                "report_id": matched_report_id,
                "lead_id": lead_id,
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("report_links").insert(link).execute()
            created += 1
        except:
            pass  # Silently skip duplicates
    
    # Summary
    print("\n" + "="*70)
    print("📊 LINKING COMPLETE")
    print("="*70)
    print(f"✅ New links created:    {created}")
    print(f"⏭️  Already existed:      {skipped}")
    print(f"⚠️  No match found:       {no_match}")
    
    # Final count
    final_result = supabase.table("report_links").select("id", count='exact').execute()
    print(f"\n📊 Total links in database: {final_result.count}")
    print(f"📊 Match rate: {final_result.count}/{len(df)} ({100*final_result.count/len(df):.1f}%)")
    print("="*70)

if __name__ == "__main__":
    main()
