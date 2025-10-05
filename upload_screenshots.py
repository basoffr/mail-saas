# -*- coding: utf-8 -*-
"""
UPLOAD SCREENSHOTS - Upload to Supabase & Link to Leads
Upload all screenshots to assets bucket and create asset records
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
SCREENSHOTS_DIR = BASE_DIR / "Importable data" / "screenshots"

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
    print("="*70)
    print("📸 UPLOAD SCREENSHOTS TO SUPABASE")
    print("="*70)
    
    start_time = time.time()
    
    # Get all screenshots
    screenshot_files = list(SCREENSHOTS_DIR.glob("*.*"))
    print(f"\n✅ Found {len(screenshot_files)} screenshots in folder")
    
    if not screenshot_files:
        print("\n❌ No screenshots found!")
        return
    
    # Check existing assets
    print("\n🔍 Checking existing assets...")
    try:
        existing_result = supabase.table("assets").select("key").execute()
        existing_keys = {r['key'] for r in existing_result.data}
        print(f"✅ Found {len(existing_keys)} existing assets")
    except:
        existing_keys = set()
    
    # Calculate what needs uploading
    to_upload = [f for f in screenshot_files if f.name not in existing_keys]
    print(f"\n📊 Status:")
    print(f"   - Total screenshots: {len(screenshot_files)}")
    print(f"   - Already uploaded: {len(existing_keys)}")
    print(f"   - To upload: {len(to_upload)}")
    
    if not to_upload:
        print("\n🎉 All screenshots already uploaded!")
        return
    
    # Upload
    print(f"\n🚀 Starting upload of {len(to_upload)} screenshots...")
    print("="*70)
    
    for screenshot_file in tqdm(to_upload, desc="Uploading"):
        try:
            asset_id = generate_id("asset", screenshot_file.name)
            checksum = calculate_checksum(screenshot_file)
            
            # Determine MIME type
            ext = screenshot_file.suffix.lower()
            mime_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.webp': 'image/webp'
            }
            mime_type = mime_map.get(ext, 'image/png')
            
            # Storage path
            storage_path = f"screenshots/{screenshot_file.name}"
            
            # Upload to storage
            with open(screenshot_file, "rb") as f:
                file_data = f.read()
                supabase.storage.from_("assets").upload(
                    storage_path,
                    file_data,
                    {"content-type": mime_type, "upsert": "true"}
                )
            
            # Insert into assets table
            asset = {
                "id": asset_id,
                "key": screenshot_file.name,
                "mime": mime_type,
                "size": screenshot_file.stat().st_size,
                "checksum": checksum,
                "storage_path": storage_path,
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("assets").insert(asset).execute()
            stats["uploaded"] += 1
            
        except Exception as e:
            stats["failed"] += 1
            if stats["failed"] <= 5:
                tqdm.write(f"⚠️  Failed: {screenshot_file.name[:40]}... - {str(e)[:60]}")
            continue
    
    # Final stats
    duration = time.time() - start_time
    print("\n" + "="*70)
    print("📊 UPLOAD COMPLETE")
    print("="*70)
    print(f"✅ Uploaded:  {stats['uploaded']}")
    print(f"⚠️  Failed:    {stats['failed']}")
    print(f"\n⏱️  Duration:  {duration:.1f} seconds")
    
    # Final count
    final_result = supabase.table("assets").select("id", count='exact').execute()
    print(f"📊 Total assets in database: {final_result.count}")
    print("="*70)
    
    print("\n📋 NEXT: Link screenshots to leads using URL matching")
    print("   Run: python link_screenshots_to_leads.py")

if __name__ == "__main__":
    main()
