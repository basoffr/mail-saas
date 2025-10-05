# -*- coding: utf-8 -*-
"""
EXTRACT SCREENSHOTS - Handle long filenames
Extract screenshots.zip and rename to shorter names
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import zipfile
import hashlib
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).parent
ZIP_FILE = BASE_DIR / "Importable data" / "screenshots.zip"
EXTRACT_TO = BASE_DIR / "Importable data" / "screenshots"

def short_name(original_name: str) -> str:
    """Generate short but unique filename"""
    # Get extension
    ext = Path(original_name).suffix or '.png'
    
    # Extract domain from filename (first part before _)
    parts = Path(original_name).stem.split('_')
    domain = parts[0] if parts else 'screenshot'
    
    # Create hash for uniqueness
    hash_suffix = hashlib.md5(original_name.encode()).hexdigest()[:8]
    
    return f"{domain}_{hash_suffix}{ext}"

def main():
    print("="*70)
    print("📸 EXTRACT SCREENSHOTS")
    print("="*70)
    
    # Create extract folder
    EXTRACT_TO.mkdir(parents=True, exist_ok=True)
    
    # Open ZIP
    print(f"\n📦 Opening ZIP: {ZIP_FILE.name}")
    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        files = [f for f in zip_ref.namelist() if not f.endswith('/')]
        print(f"✅ Found {len(files)} files in ZIP")
        
        extracted = 0
        skipped = 0
        failed = 0
        
        # Extract with progress
        print("\n🚀 Extracting files...")
        for file_info in tqdm(files, desc="Extracting"):
            try:
                # Generate short name
                short_filename = short_name(file_info)
                target_path = EXTRACT_TO / short_filename
                
                # Skip if exists
                if target_path.exists():
                    skipped += 1
                    continue
                
                # Extract
                data = zip_ref.read(file_info)
                target_path.write_bytes(data)
                extracted += 1
                
            except Exception as e:
                failed += 1
                if failed <= 5:
                    tqdm.write(f"⚠️  Failed: {file_info[:50]}... - {str(e)[:50]}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 EXTRACTION COMPLETE")
    print("="*70)
    print(f"✅ Extracted:  {extracted}")
    print(f"⏭️  Skipped:    {skipped}")
    print(f"⚠️  Failed:     {failed}")
    
    # Verify
    actual_files = list(EXTRACT_TO.glob("*.*"))
    print(f"\n📊 Total files in folder: {len(actual_files)}")
    print("="*70)

if __name__ == "__main__":
    main()
