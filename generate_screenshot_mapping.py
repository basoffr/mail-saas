"""
Generate SQL to map screenshots to leads based on local filenames
"""
import os
import re
from pathlib import Path

# Path to screenshots directory
SCREENSHOTS_DIR = Path(r"c:\Users\basof\OneDrive\Documenten\Punthelder\Mail dashboard\Importable data\screenshots")

def normalize_for_matching(text):
    """Normalize text for domain matching"""
    # Remove common prefixes/suffixes
    text = text.lower()
    text = text.replace('www_', '').replace('www.', '')
    text = text.replace('.nl', '').replace('.com', '').replace('.be', '')
    text = text.replace('-', '').replace('_', '')
    return text

def extract_domain_from_filename(filename):
    """Extract potential domain from screenshot filename"""
    # Remove .png extension and hash
    base = filename.replace('.png', '')
    
    # Split on underscore to get domain part (before hash)
    parts = base.split('_')
    if len(parts) >= 2:
        # Domain is everything except the last part (hash)
        domain_part = '_'.join(parts[:-1])
        return domain_part
    return base

def generate_sql_updates():
    """Generate SQL UPDATE statements for screenshot mapping"""
    
    # Get all screenshot files
    screenshots = []
    for file in SCREENSHOTS_DIR.glob("*.png"):
        if file.is_file():
            screenshots.append(file.name)
    
    print("-- SQL UPDATE statements to map screenshots to leads")
    print(f"-- Found {len(screenshots)} screenshots\n")
    print("BEGIN;\n")
    
    # Generate CASE statement for bulk update
    print("UPDATE leads")
    print("SET image_key = CASE")
    
    for screenshot in sorted(screenshots):
        domain_part = extract_domain_from_filename(screenshot)
        
        # Generate SQL condition
        # Try different matching patterns
        normalized = normalize_for_matching(domain_part)
        
        print(f"  WHEN REPLACE(REPLACE(REPLACE(LOWER(domain), '.nl', ''), '.com', ''), '-', '') LIKE '%{normalized}%' THEN '{screenshot}'")
    
    print("  ELSE image_key")
    print("END")
    print("WHERE image_key IS NULL;\n")
    
    print("-- Verify results")
    print("SELECT COUNT(*) as total_updated FROM leads WHERE image_key IS NOT NULL;\n")
    
    print("COMMIT;")

if __name__ == "__main__":
    generate_sql_updates()
