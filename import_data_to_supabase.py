# -*- coding: utf-8 -*-
"""
SUPABASE DATA IMPORT SCRIPT
============================
Import 2100+ leads, reports, and screenshots to Supabase

Usage:
    python import_data_to_supabase.py

Requirements:
    pip install supabase pandas python-dotenv tqdm
"""

import os
import sys
import io

# Set UTF-8 encoding for console output (Windows fix)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
from tqdm import tqdm
import time

# Configuration
SUPABASE_URL = "https://zpnklihryhpkaiyubkfn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDMzNDIsImV4cCI6MjA3NDcxOTM0Mn0.P8Rx3r--uu8V-HCEH2s5qH3Ud0HhpLBUWaidrahO0jY"

# Paths
BASE_DIR = Path(__file__).parent
EXCEL_FILE = BASE_DIR / "Importable data" / "leads_transformed_v2.xlsx"
REPORTS_DIR = BASE_DIR / "Importable data" / "rapporten_pdf"
SCREENSHOTS_ZIP = BASE_DIR / "Importable data" / "screenshots.zip"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Statistics
stats = {
    "leads_imported": 0,
    "leads_skipped": 0,
    "reports_uploaded": 0,
    "reports_failed": 0,
    "assets_uploaded": 0,
    "assets_failed": 0,
    "links_created": 0,
}


def generate_id(prefix: str, unique_string: str) -> str:
    """Generate a unique ID with prefix"""
    hash_suffix = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    return f"{prefix}_{hash_suffix}"


def extract_domain(url: str) -> str:
    """Extract domain from URL for matching"""
    # Remove protocol
    domain = url.replace("https://", "").replace("http://", "")
    # Remove www
    domain = domain.replace("www.", "")
    # Remove trailing slash and path
    domain = domain.split("/")[0]
    # Remove port
    domain = domain.split(":")[0]
    return domain


def calculate_checksum(file_path: Path) -> str:
    """Calculate MD5 checksum of file"""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def import_leads() -> Dict[str, str]:
    """
    Import leads from Excel to Supabase
    Returns: dict mapping email -> lead_id
    """
    print("\n📊 STEP 1: Importing Leads from Excel...")
    
    if not EXCEL_FILE.exists():
        print(f"❌ Excel file not found: {EXCEL_FILE}")
        return {}
    
    # Read Excel
    df = pd.read_excel(EXCEL_FILE)
    print(f"   Found {len(df)} leads in Excel")
    
    # Map email -> lead_id
    email_to_lead_id = {}
    
    # Process in batches of 100
    batch_size = 100
    for i in tqdm(range(0, len(df), batch_size), desc="Importing leads"):
        batch = df.iloc[i:i+batch_size]
        
        leads_to_insert = []
        for _, row in batch.iterrows():
            email = row['email']
            url = row.get('url', '')
            company = row.get('company', '')
            
            # Generate lead ID
            lead_id = generate_id("lead", email)
            email_to_lead_id[email] = lead_id
            
            # Extract domain from URL
            domain = extract_domain(url) if url else None
            
            # Create vars JSONB
            vars_data = {
                "keyword": row.get('keyword', ''),
                "google_rank": str(row.get('google_rank', '')),
                "seo_score": str(row.get('seo_score', ''))
            }
            
            # Create lead object
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
            # Insert batch
            supabase.table("leads").insert(leads_to_insert).execute()
            stats["leads_imported"] += len(leads_to_insert)
        except Exception as e:
            print(f"\n⚠️  Error inserting batch: {e}")
            stats["leads_skipped"] += len(leads_to_insert)
            continue
    
    print(f"✅ Imported {stats['leads_imported']} leads")
    if stats['leads_skipped'] > 0:
        print(f"⚠️  Skipped {stats['leads_skipped']} leads (duplicates/errors)")
    
    return email_to_lead_id


def upload_reports(email_to_lead_id: Dict[str, str]) -> Dict[str, str]:
    """
    Upload PDF reports to Supabase Storage
    Returns: dict mapping filename -> report_id
    """
    print("\n📄 STEP 2: Uploading PDF Reports...")
    
    if not REPORTS_DIR.exists():
        print(f"❌ Reports directory not found: {REPORTS_DIR}")
        return {}
    
    # Get all PDF files
    pdf_files = list(REPORTS_DIR.glob("*.pdf"))
    print(f"   Found {len(pdf_files)} PDF files")
    
    # Check which reports already exist in database
    try:
        existing = supabase.table("reports").select("id,filename").execute()
        existing_filenames = {r['filename'] for r in existing.data}
        print(f"   Found {len(existing_filenames)} existing reports in database")
    except:
        existing_filenames = set()
    
    filename_to_report_id = {}
    
    for pdf_file in tqdm(pdf_files, desc="Uploading reports"):
        try:
            # Skip if already exists
            if pdf_file.name in existing_filenames:
                stats["reports_uploaded"] += 1  # Count as success
                report_id = generate_id("report", pdf_file.stem)
                filename_to_report_id[pdf_file.stem] = report_id
                continue
            
            # Generate report ID
            report_id = generate_id("report", pdf_file.stem)
            filename_to_report_id[pdf_file.stem] = report_id
            
            # Calculate checksum
            checksum = calculate_checksum(pdf_file)
            
            # Storage path
            storage_path = f"reports/{report_id}.pdf"
            
            # Upload to Supabase Storage
            with open(pdf_file, "rb") as f:
                file_data = f.read()
                supabase.storage.from_("reports").upload(
                    storage_path,
                    file_data,
                    {"content-type": "application/pdf"}
                )
            
            # Insert into reports table
            report = {
                "id": report_id,
                "filename": pdf_file.name,
                "type": "pdf",
                "size_bytes": pdf_file.stat().st_size,
                "storage_path": storage_path,
                "checksum": checksum,
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("reports").insert(report).execute()
            stats["reports_uploaded"] += 1
            
        except Exception as e:
            print(f"\n⚠️  Failed to upload {pdf_file.name}: {e}")
            stats["reports_failed"] += 1
            continue
    
    print(f"✅ Uploaded {stats['reports_uploaded']} reports")
    if stats['reports_failed'] > 0:
        print(f"⚠️  Failed {stats['reports_failed']} reports")
    
    return filename_to_report_id


def link_reports_to_leads(
    email_to_lead_id: Dict[str, str],
    filename_to_report_id: Dict[str, str]
) -> None:
    """
    Create report_links between reports and leads based on filename matching
    """
    print("\n🔗 STEP 3: Linking Reports to Leads...")
    
    # Read Excel to get URL to email mapping
    df = pd.read_excel(EXCEL_FILE)
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Creating links"):
        email = row['email']
        url = row.get('url', '')
        
        if not url or email not in email_to_lead_id:
            continue
        
        # Extract domain and try to match with report filename
        domain = extract_domain(url)
        
        # Try to find matching report
        # Report filename format: "domain_report.pdf" or "domain_with_path_report.pdf"
        potential_matches = [
            domain.replace(".", "_"),
            domain.replace(".", "_") + "_report",
            url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")
        ]
        
        matched_report_id = None
        for match in potential_matches:
            for filename, report_id in filename_to_report_id.items():
                if match in filename.lower():
                    matched_report_id = report_id
                    break
            if matched_report_id:
                break
        
        if matched_report_id:
            try:
                # Create link
                link_id = generate_id("link", f"{matched_report_id}_{email}")
                link = {
                    "id": link_id,
                    "report_id": matched_report_id,
                    "lead_id": email_to_lead_id[email],
                    "created_at": datetime.utcnow().isoformat()
                }
                
                supabase.table("report_links").insert(link).execute()
                stats["links_created"] += 1
            except Exception as e:
                # Silently skip duplicate links
                pass
    
    print(f"✅ Created {stats['links_created']} report-lead links")


def import_screenshots_placeholder():
    """
    Placeholder for screenshot import
    Note: Screenshots need to be extracted from ZIP first
    """
    print("\n📸 STEP 4: Screenshots Import...")
    print("⚠️  Screenshot import requires manual ZIP extraction first")
    print(f"   ZIP file: {SCREENSHOTS_ZIP}")
    print("   Extract to: Importable data/screenshots/")
    print("   Then update this script to process the images")


def main():
    """Main import process"""
    print("=" * 60)
    print("🚀 SUPABASE DATA IMPORT")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Step 1: Import leads
        email_to_lead_id = import_leads()
        
        # Step 2: Upload reports
        filename_to_report_id = upload_reports(email_to_lead_id)
        
        # Step 3: Link reports to leads
        link_reports_to_leads(email_to_lead_id, filename_to_report_id)
        
        # Step 4: Screenshots (placeholder)
        import_screenshots_placeholder()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print final statistics
    duration = time.time() - start_time
    print("\n" + "=" * 60)
    print("📊 IMPORT COMPLETE")
    print("=" * 60)
    print(f"✅ Leads imported:     {stats['leads_imported']}")
    print(f"⚠️  Leads skipped:      {stats['leads_skipped']}")
    print(f"✅ Reports uploaded:   {stats['reports_uploaded']}")
    print(f"⚠️  Reports failed:     {stats['reports_failed']}")
    print(f"✅ Links created:      {stats['links_created']}")
    print(f"\n⏱️  Total time: {duration:.1f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    main()
