# -*- coding: utf-8 -*-
"""
FRESH IMPORT - Complete Clean Import
Import all 2134 leads + create report links + prepare for screenshots
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict
import pandas as pd
from supabase import create_client, Client
from tqdm import tqdm
import time

# Configuration
SUPABASE_URL = "https://zpnklihryhpkaiyubkfn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDMzNDIsImV4cCI6MjA3NDcxOTM0Mn0.P8Rx3r--uu8V-HCEH2s5qH3Ud0HhpLBUWaidrahO0jY"

BASE_DIR = Path(__file__).parent
EXCEL_FILE = BASE_DIR / "Importable data" / "leads_transformed_v2.xlsx"
REPORTS_DIR = BASE_DIR / "Importable data" / "rapporten_pdf"

# Initialize
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

stats = {
    "leads_imported": 0,
    "leads_failed": 0,
    "links_created": 0,
    "links_failed": 0
}

def generate_id(prefix: str, unique_string: str) -> str:
    hash_suffix = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    return f"{prefix}_{hash_suffix}"

def extract_domain(url: str) -> str:
    """Extract clean domain from URL"""
    if not url:
        return None
    domain = url.replace("https://", "").replace("http://", "")
    domain = domain.replace("www.", "")
    domain = domain.split("/")[0]
    domain = domain.split(":")[0]
    return domain

def import_leads() -> Dict[str, str]:
    """Import all 2134 leads from Excel"""
    print("\n" + "="*70)
    print("📊 STEP 1: IMPORTING LEADS")
    print("="*70)
    
    # Read Excel
    df = pd.read_excel(EXCEL_FILE)
    print(f"✅ Found {len(df)} leads in Excel")
    
    email_to_lead_id = {}
    
    # Process in batches
    batch_size = 50
    total_batches = (len(df) + batch_size - 1) // batch_size
    
    for i in tqdm(range(0, len(df), batch_size), total=total_batches, desc="Importing"):
        batch = df.iloc[i:i+batch_size]
        leads_to_insert = []
        
        for _, row in batch.iterrows():
            email = row['email']
            url = row.get('url', '')
            company = row.get('company', '')
            
            lead_id = generate_id("lead", email)
            email_to_lead_id[email] = lead_id
            
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
            leads_to_insert.append(lead)
        
        try:
            supabase.table("leads").insert(leads_to_insert).execute()
            stats["leads_imported"] += len(leads_to_insert)
        except Exception as e:
            stats["leads_failed"] += len(leads_to_insert)
            tqdm.write(f"⚠️  Batch failed: {str(e)[:100]}")
    
    print(f"\n✅ Imported {stats['leads_imported']} leads")
    if stats["leads_failed"] > 0:
        print(f"⚠️  Failed {stats['leads_failed']} leads")
    
    return email_to_lead_id

def create_report_links(email_to_lead_id: Dict[str, str]):
    """Create report_links between reports and leads"""
    print("\n" + "="*70)
    print("🔗 STEP 2: CREATING REPORT LINKS")
    print("="*70)
    
    # Get all existing reports
    reports_result = supabase.table("reports").select("id,filename").execute()
    reports = {r['filename']: r['id'] for r in reports_result.data}
    print(f"✅ Found {len(reports)} reports in database")
    
    # Read Excel for URL mapping
    df = pd.read_excel(EXCEL_FILE)
    
    matched = 0
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Linking"):
        email = row['email']
        url = row.get('url', '')
        
        if not url or email not in email_to_lead_id:
            continue
        
        lead_id = email_to_lead_id[email]
        domain = extract_domain(url)
        
        if not domain:
            continue
        
        # Try to find matching report
        # Match patterns: domain_com_report.pdf or subdomain_domain_com_report.pdf
        domain_pattern = domain.replace(".", "_")
        
        matched_report_id = None
        for filename, report_id in reports.items():
            filename_lower = filename.lower().replace(".pdf", "")
            if domain_pattern in filename_lower or domain.replace(".", "_") in filename_lower:
                matched_report_id = report_id
                break
        
        if matched_report_id:
            try:
                link_id = generate_id("link", f"{matched_report_id}_{lead_id}")
                link = {
                    "id": link_id,
                    "report_id": matched_report_id,
                    "lead_id": lead_id,
                    "created_at": datetime.utcnow().isoformat()
                }
                supabase.table("report_links").insert(link).execute()
                stats["links_created"] += 1
                matched += 1
            except:
                stats["links_failed"] += 1
    
    print(f"\n✅ Created {stats['links_created']} report links")
    print(f"📊 Match rate: {matched}/{len(df)} ({100*matched/len(df):.1f}%)")

def main():
    print("\n" + "="*70)
    print("🚀 FRESH IMPORT - ALL DATA")
    print("="*70)
    
    start_time = time.time()
    
    # Step 1: Import leads
    email_to_lead_id = import_leads()
    
    # Step 2: Create report links
    create_report_links(email_to_lead_id)
    
    # Final stats
    duration = time.time() - start_time
    
    print("\n" + "="*70)
    print("📊 IMPORT COMPLETE")
    print("="*70)
    print(f"✅ Leads imported:     {stats['leads_imported']}")
    print(f"⚠️  Leads failed:       {stats['leads_failed']}")
    print(f"✅ Links created:      {stats['links_created']}")
    print(f"⚠️  Links failed:       {stats['links_failed']}")
    print(f"\n⏱️  Total time: {duration:.1f} seconds")
    print("="*70)
    
    print("\n📸 NEXT STEP: Screenshots")
    print("   1. Extract: Importable data/screenshots.zip")
    print("   2. Run: python upload_screenshots.py")

if __name__ == "__main__":
    main()
