"""
Migratie Script: Reports van Supabase Storage naar Database
============================================================

Dit script:
1. Haalt alle files uit Supabase Storage bucket 'reports/'
2. Maakt records aan in de 'reports' table
3. Linkt reports aan leads via 'report_links' (gebaseerd op domain matching)

Gebruik:
    python scripts/migrate_reports_to_db.py

Environment variables nodig:
    - SUPABASE_URL
    - SUPABASE_SERVICE_ROLE_KEY (of SUPABASE_ANON_KEY)
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Initialize Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise Exception("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    
    return create_client(url, key)


def extract_domain_from_filename(filename: str) -> str:
    """
    Extract domain from filename.
    Examples:
        'example.com_report.pdf' -> 'example.com'
        'www.example.nl_seo.pdf' -> 'example.nl'
        'domain-report.pdf' -> 'domain'
    """
    # Remove extension
    name_without_ext = filename.rsplit('.', 1)[0]
    
    # Common patterns: domain_report, domain-report, domain.report
    # Try to extract domain (first part before underscore or dash)
    parts = name_without_ext.replace('-', '_').split('_')
    
    if parts:
        potential_domain = parts[0]
        # Clean www. prefix
        if potential_domain.startswith('www.'):
            potential_domain = potential_domain[4:]
        return potential_domain
    
    return name_without_ext


def get_file_type(filename: str) -> str:
    """Get file type from extension."""
    ext = filename.lower().rsplit('.', 1)[-1]
    valid_types = ['pdf', 'xlsx', 'png', 'jpg', 'jpeg']
    return ext if ext in valid_types else 'pdf'


def migrate_reports(dry_run: bool = False):
    """
    Migrate reports from Supabase Storage to database.
    
    Args:
        dry_run: If True, only shows what would be migrated without making changes
    """
    supabase = get_supabase_client()
    
    logger.info("🚀 Starting reports migration...")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    
    # Step 1: List all files in reports bucket
    logger.info("\n📁 Step 1: Listing files in 'reports' bucket...")
    try:
        files_result = supabase.storage.from_('reports').list()
        logger.info(f"Found {len(files_result)} files in storage")
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        return
    
    # Step 2: Check existing reports in database
    logger.info("\n📊 Step 2: Checking existing reports in database...")
    try:
        existing_result = supabase.table('reports').select('storage_path').execute()
        existing_paths = {row['storage_path'] for row in existing_result.data}
        logger.info(f"Found {len(existing_paths)} existing reports in database")
    except Exception as e:
        logger.error(f"Failed to check existing reports: {e}")
        existing_paths = set()
    
    # Step 3: Migrate files
    logger.info("\n🔄 Step 3: Migrating reports to database...")
    
    migrated_count = 0
    skipped_count = 0
    failed_count = 0
    
    for file_obj in files_result:
        filename = file_obj['name']
        storage_path = filename  # Storage path in bucket
        
        # Skip if already exists
        if storage_path in existing_paths:
            logger.debug(f"⏭️  Skip (exists): {filename}")
            skipped_count += 1
            continue
        
        # Get file metadata
        try:
            # Get file size from metadata
            size_bytes = file_obj.get('metadata', {}).get('size', 0)
            if not size_bytes:
                # Fallback: try to get from file info
                size_bytes = 0
            
            # Determine file type
            file_type = get_file_type(filename)
            
            # Extract domain for potential linking
            domain = extract_domain_from_filename(filename)
            
            if dry_run:
                logger.info(f"[DRY RUN] Would migrate: {filename} ({size_bytes} bytes, type: {file_type}, domain: {domain})")
                migrated_count += 1
                continue
            
            # Create report record
            report_id = str(uuid.uuid4())
            report_data = {
                'id': report_id,
                'filename': filename,
                'type': file_type,
                'size_bytes': size_bytes,
                'storage_path': storage_path,
                'checksum': None,  # Could compute from file content if needed
                'created_at': datetime.utcnow().isoformat(),
                'uploaded_by': 'migration_script',
                'meta': {'migrated_from_storage': True, 'extracted_domain': domain}
            }
            
            # Insert to database
            supabase.table('reports').insert(report_data).execute()
            logger.info(f"✅ Migrated: {filename} (domain: {domain})")
            migrated_count += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate {filename}: {e}")
            failed_count += 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 MIGRATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total files in storage: {len(files_result)}")
    logger.info(f"Already in database:    {skipped_count}")
    logger.info(f"Migrated:               {migrated_count}")
    logger.info(f"Failed:                 {failed_count}")
    logger.info("="*60)
    
    if not dry_run and migrated_count > 0:
        logger.info("\n🔗 Step 4: Auto-linking reports to leads...")
        link_reports_to_leads(supabase)
    
    logger.info("\n✅ Migration completed!")


def link_reports_to_leads(supabase: Client):
    """
    Auto-link reports to leads based on domain matching.
    
    Logic:
    1. For each report, extract domain from filename
    2. Find lead with matching domain
    3. Create report_link entry
    """
    logger.info("Starting auto-linking process...")
    
    try:
        # Get all reports without links
        reports_result = supabase.table('reports').select('id, filename, meta').execute()
        reports = reports_result.data
        
        # Get all leads
        leads_result = supabase.table('leads').select('id, domain, email').execute()
        leads = {lead['domain']: lead['id'] for lead in leads_result.data if lead.get('domain')}
        
        logger.info(f"Found {len(reports)} reports and {len(leads)} leads with domains")
        
        linked_count = 0
        
        for report in reports:
            report_id = report['id']
            filename = report['filename']
            meta = report.get('meta', {})
            
            # Try to get domain from meta or extract from filename
            domain = None
            if isinstance(meta, dict):
                domain = meta.get('extracted_domain')
            
            if not domain:
                domain = extract_domain_from_filename(filename)
            
            # Find matching lead
            lead_id = leads.get(domain)
            
            if lead_id:
                # Check if link already exists
                existing_link = supabase.table('report_links').select('id').eq('report_id', report_id).execute()
                
                if not existing_link.data:
                    # Create link
                    link_data = {
                        'id': str(uuid.uuid4()),
                        'report_id': report_id,
                        'lead_id': lead_id,
                        'campaign_id': None,
                        'created_at': datetime.utcnow().isoformat()
                    }
                    
                    supabase.table('report_links').insert(link_data).execute()
                    logger.info(f"🔗 Linked: {filename} → lead (domain: {domain})")
                    linked_count += 1
        
        logger.info(f"\n✅ Auto-linked {linked_count} reports to leads")
        
    except Exception as e:
        logger.error(f"❌ Auto-linking failed: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate reports from Supabase Storage to database')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without making changes')
    parser.add_argument('--link-only', action='store_true', help='Only run auto-linking, skip migration')
    
    args = parser.parse_args()
    
    try:
        if args.link_only:
            logger.info("🔗 Running auto-linking only...")
            supabase = get_supabase_client()
            link_reports_to_leads(supabase)
        else:
            migrate_reports(dry_run=args.dry_run)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
