# -*- coding: utf-8 -*-
"""
UPLOAD REPORTS ONLY - Dedicated script
Upload PDF reports to Supabase Storage (resumes from where it left off)
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import hashlib
from pathlib import Path
from datetime import datetime
from supabase import create_client, Client
from tqdm import tqdm
import time

# Configuration
SUPABASE_URL = "https://zpnklihryhpkaiyubkfn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDMzNDIsImV4cCI6MjA3NDcxOTM0Mn0.P8Rx3r--uu8V-HCEH2s5qH3Ud0HhpLBUWaidrahO0jY"

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "Importable data" / "rapporten_pdf"

# Initialize
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

stats = {
    "uploaded": 0,
    "skipped": 0,
    "failed": 0
}

def generate_id(prefix: str, unique_string: str) -> str:
    hash_suffix = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    return f"{prefix}_{hash_suffix}"

def calculate_checksum(file_path: Path) -> str:
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()

def main():
    print("=" * 70)
    print("📄 UPLOAD REPORTS TO SUPABASE")
    print("=" * 70)
    
    start_time = time.time()
    
    # Get all PDFs
    pdf_files = list(REPORTS_DIR.glob("*.pdf"))
    print(f"\n✅ Found {len(pdf_files)} PDF files in {REPORTS_DIR.name}/")
    
    # Check existing
    print("\n🔍 Checking existing reports in database...")
    try:
        existing = supabase.table("reports").select("id,filename").execute()
        existing_filenames = {r['filename'] for r in existing.data}
        print(f"✅ Found {len(existing_filenames)} existing reports")
    except Exception as e:
        print(f"⚠️  Error checking existing: {e}")
        existing_filenames = set()
    
    # Calculate what needs uploading
    to_upload = [f for f in pdf_files if f.name not in existing_filenames]
    print(f"\n📊 Status:")
    print(f"   - Total PDFs: {len(pdf_files)}")
    print(f"   - Already uploaded: {len(existing_filenames)}")
    print(f"   - To upload: {len(to_upload)}")
    
    if not to_upload:
        print("\n🎉 All reports already uploaded!")
        return
    
    # Upload remaining
    print(f"\n🚀 Starting upload of {len(to_upload)} reports...")
    print("=" * 70)
    
    for pdf_file in tqdm(to_upload, desc="Uploading"):
        try:
            report_id = generate_id("report", pdf_file.stem)
            checksum = calculate_checksum(pdf_file)
            storage_path = f"reports/{report_id}.pdf"
            
            # Upload to storage
            with open(pdf_file, "rb") as f:
                file_data = f.read()
                supabase.storage.from_("reports").upload(
                    storage_path,
                    file_data,
                    {"content-type": "application/pdf", "upsert": "true"}
                )
            
            # Insert into database
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
            stats["uploaded"] += 1
            
        except Exception as e:
            stats["failed"] += 1
            tqdm.write(f"⚠️  Failed: {pdf_file.name[:50]}... - {str(e)[:100]}")
            continue
    
    # Final stats
    duration = time.time() - start_time
    print("\n" + "=" * 70)
    print("📊 UPLOAD COMPLETE")
    print("=" * 70)
    print(f"✅ Uploaded:  {stats['uploaded']}")
    print(f"⚠️  Failed:    {stats['failed']}")
    print(f"⏱️  Duration:  {duration:.1f} seconds")
    print("=" * 70)

if __name__ == "__main__":
    main()
