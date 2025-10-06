"""
Bulk Import Service - Importeer Leads + Screenshots + Reports in één keer

Functionaliteit:
- Upload Excel met leads + variabelen
- Upload Screenshots folder (ZIP)
- Upload Reports folder (ZIP)
- Automatische linking op basis van normalized domain
- Alle leads krijgen een list_name voor groepering
"""

import io
import zipfile
import re
import uuid
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from loguru import logger
from fastapi import UploadFile

from app.models.lead import Lead
from app.services.supabase_storage import supabase_storage
from supabase import create_client
import os


class BulkImportService:
    """Service voor bulk import van leads + assets"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Service key voor admin access
        
        if self.supabase_url and self.supabase_key:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
        else:
            self.supabase = None
            logger.warning("Supabase not configured for bulk import")
    
    def normalize_domain(self, domain: str) -> str:
        """
        Normalize domain voor matching
        
        Examples:
            "labelnoir.nl" -> "labelnoir"
            "www.123hair.nl" -> "123hair"
            "example.com" -> "example"
        """
        domain = domain.lower().strip()
        domain = domain.replace('www.', '')
        domain = domain.replace('.nl', '').replace('.com', '').replace('.be', '')
        domain = domain.replace('-', '').replace('_', '')
        return domain
    
    def extract_domain_from_filename(self, filename: str) -> str:
        """
        Extract domain from filename
        
        Examples:
            "labelnoir_40e03960.png" -> "labelnoir"
            "123hair_cca1df84.png" -> "123hair"
        """
        # Remove extension
        base = filename.replace('.png', '').replace('.jpg', '').replace('.pdf', '')
        
        # Split on underscore, take first part
        parts = base.split('_')
        if len(parts) >= 1:
            return parts[0]
        return base
    
    async def process_bulk_import(
        self,
        excel_file: UploadFile,
        screenshots_zip: Optional[UploadFile],
        reports_zip: Optional[UploadFile],
        list_name: str
    ) -> Dict[str, Any]:
        """
        Process complete bulk import
        
        Args:
            excel_file: Excel bestand met leads + variabelen
            screenshots_zip: ZIP met screenshots
            reports_zip: ZIP met reports
            list_name: Naam voor deze import batch
        
        Returns:
            {
                "leads_imported": 100,
                "screenshots_uploaded": 95,
                "reports_uploaded": 98,
                "leads_complete": 90,  # Leads met alles
                "warnings": []
            }
        """
        result = {
            "leads_imported": 0,
            "screenshots_uploaded": 0,
            "reports_uploaded": 0,
            "leads_complete": 0,
            "warnings": []
        }
        
        try:
            # Step 1: Upload screenshots en reports naar Supabase Storage
            screenshot_files = {}
            report_files = {}
            
            if screenshots_zip:
                screenshot_files = await self._upload_zip_to_storage(
                    screenshots_zip, 
                    "screenshots"
                )
                result["screenshots_uploaded"] = len(screenshot_files)
            
            if reports_zip:
                report_files = await self._upload_zip_to_storage(
                    reports_zip,
                    "reports"
                )
                result["reports_uploaded"] = len(report_files)
            
            # Step 2: Parse Excel en create leads
            excel_content = await excel_file.read()
            df = pd.read_excel(io.BytesIO(excel_content))
            
            # Log kolommen voor debugging
            logger.info(f"Excel columns found: {list(df.columns)}")
            logger.info(f"Total rows in Excel: {len(df)}")
            
            # Create case-insensitive column mapping
            col_map = {col.lower().strip(): col for col in df.columns}
            logger.info(f"Column mapping (lowercase): {list(col_map.keys())}")
            
            def get_col_value(row, *possible_names):
                """Get value from row with case-insensitive column matching"""
                for name in possible_names:
                    # Try exact match first
                    if name in row:
                        val = row[name]
                        if pd.notna(val) and str(val).strip():
                            return str(val).strip()
                    # Try lowercase match
                    name_lower = name.lower().strip()
                    if name_lower in col_map:
                        actual_col = col_map[name_lower]
                        val = row[actual_col]
                        if pd.notna(val) and str(val).strip():
                            return str(val).strip()
                return ''
            
            leads_data = []
            
            for idx, row in df.iterrows():
                try:
                    # Extract lead data with flexible column matching
                    email = get_col_value(row, 'email', 'Email', 'EMAIL', 'E-mail', 'e-mail', 'Mail')
                    url = get_col_value(row, 'url', 'URL', 'website', 'Website', 'Link')
                    domain = get_col_value(row, 'domain', 'Domain', 'DOMAIN')
                    company = get_col_value(row, 'company', 'Company', 'COMPANY', 'Bedrijfsnaam', 'bedrijfsnaam', 'Bedrijf')
                    
                    # Als geen domain kolom, extract uit URL of email
                    if not domain:
                        if url:
                            # Extract domain from URL: https://example.com/path -> example.com
                            match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', url)
                            if match:
                                domain = match.group(1)
                        elif email:
                            # Extract domain from email: user@example.com -> example.com
                            domain = email.split('@')[-1] if '@' in email else ''
                    
                    if not email:
                        result["warnings"].append(f"Row {idx+2}: Missing email")
                        continue
                    
                    if not domain:
                        result["warnings"].append(f"Row {idx+2}: Could not determine domain from URL or email")
                        continue
                    
                    # Normalize domain voor matching
                    normalized = self.normalize_domain(domain)
                    
                    # Find matching screenshot
                    image_key = None
                    for filename in screenshot_files.keys():
                        file_domain = self.extract_domain_from_filename(filename)
                        if self.normalize_domain(file_domain) == normalized:
                            image_key = filename
                            break
                    
                    # Find matching report
                    report_filename = None
                    for filename in report_files.keys():
                        file_domain = self.extract_domain_from_filename(filename)
                        if self.normalize_domain(file_domain) == normalized:
                            report_filename = filename
                            break
                    
                    # Extract variables from Excel columns
                    vars_dict = {}
                    
                    # Common variable mappings - gebruik flexible matching
                    var_mappings = {
                        'keyword': ['keyword', 'Keyword', 'zoekwoord', 'Zoekwoord', 'KEYWORD'],
                        'google_rank': ['google_rank', 'Google Rank', 'ranking', 'Ranking', 'Positie', 'positie'],
                        'seo_score': ['seo_score', 'SEO Score', 'SEO_Score', 'Score'],
                        'city': ['city', 'City', 'plaats', 'Plaats', 'Stad', 'stad'],
                        'phone': ['phone', 'Phone', 'telefoon', 'Telefoon', 'Tel', 'tel'],
                    }
                    
                    for var_name, possible_columns in var_mappings.items():
                        value = get_col_value(row, *possible_columns)
                        if value:
                            vars_dict[var_name] = value
                    
                    # Add report filename to vars if found
                    if report_filename:
                        vars_dict['report_filename'] = report_filename
                    
                    # Create lead data (created_at and updated_at are auto-generated by Supabase)
                    # Use URL from earlier or construct default
                    if not url:
                        url = f"https://{domain}"
                    
                    lead_data = {
                        "id": str(uuid.uuid4()),  # Generate UUID for Supabase
                        "email": email,
                        "domain": domain,
                        "company": company,
                        "url": url,
                        "status": "active",
                        "image_key": image_key,
                        "list_name": list_name,
                        "vars": vars_dict
                    }
                    
                    leads_data.append(lead_data)
                    
                    # Check completeness
                    if image_key and report_filename and len(vars_dict) > 1:
                        result["leads_complete"] += 1
                    
                except Exception as e:
                    result["warnings"].append(f"Row {idx+2}: {str(e)}")
                    continue
            
            # Step 3: Bulk insert leads naar Supabase
            if leads_data and self.supabase:
                try:
                    logger.info(f"Inserting {len(leads_data)} leads into Supabase...")
                    response = self.supabase.table('leads').insert(leads_data).execute()
                    result["leads_imported"] = len(leads_data)
                    logger.info(f"Successfully inserted {len(leads_data)} leads")
                    
                except Exception as e:
                    logger.error(f"Failed to insert leads: {e}")
                    logger.error(f"Error type: {type(e).__name__}")
                    logger.error(f"Error details: {str(e)}")
                    result["warnings"].append(f"Database insert failed: {str(e)}")
                    # Don't raise, continue with partial success
            elif leads_data:
                logger.warning(f"Supabase not configured, skipping database insert for {len(leads_data)} leads")
                result["warnings"].append("Supabase not configured - leads not saved to database")
            
            return result
            
        except Exception as e:
            logger.error(f"Bulk import failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return error instead of raising to prevent server crash
            return {
                "leads_imported": 0,
                "screenshots_uploaded": result.get("screenshots_uploaded", 0),
                "reports_uploaded": result.get("reports_uploaded", 0),
                "leads_complete": 0,
                "warnings": [f"Critical error: {str(e)}"]
            }
    
    async def _upload_zip_to_storage(
        self, 
        zip_file: UploadFile, 
        folder: str
    ) -> Dict[str, str]:
        """
        Upload ZIP contents naar Supabase Storage
        
        Returns:
            Dict mapping filename -> storage_path
        """
        uploaded_files = {}
        
        try:
            zip_content = await zip_file.read()
            
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                for file_info in zf.filelist:
                    # Skip directories en hidden files
                    if file_info.is_dir() or file_info.filename.startswith('__MACOSX'):
                        continue
                    
                    # Get just the filename (no path)
                    filename = os.path.basename(file_info.filename)
                    
                    if not filename:
                        continue
                    
                    # Read file content
                    file_content = zf.read(file_info.filename)
                    
                    # Upload to Supabase Storage
                    if self.supabase:
                        try:
                            storage_path = f"{folder}/{filename}"
                            
                            # Determine content type
                            content_type = "image/png" if filename.endswith('.png') else \
                                          "image/jpeg" if filename.endswith(('.jpg', '.jpeg')) else \
                                          "application/pdf" if filename.endswith('.pdf') else \
                                          "application/octet-stream"
                            
                            # Upload with upsert to overwrite existing files
                            supabase_storage.upload(
                                storage_path,
                                file_content,
                                {"content-type": content_type, "upsert": "true"}
                            )
                            
                            uploaded_files[filename] = storage_path
                            logger.info(f"Uploaded {storage_path}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to upload {filename}: {e}")
                            continue
            
        except Exception as e:
            logger.error(f"Failed to process ZIP: {e}")
            raise
        
        return uploaded_files
    
    async def clear_all_data(self):
        """
        DANGER: Verwijder alle data uit Supabase
        Gebruik alleen voor clean slate imports
        """
        if not self.supabase:
            logger.warning("Supabase not configured")
            return {"deleted_leads": 0, "deleted_files": 0}
        
        deleted_counts = {
            "deleted_leads": 0,
            "deleted_reports": 0,
            "deleted_report_links": 0,
            "deleted_assets": 0,
            "deleted_files": 0
        }
        
        try:
            # Delete all leads
            logger.info("Deleting all leads...")
            result = self.supabase.table('leads').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            deleted_counts["deleted_leads"] = len(result.data) if result.data else 0
            logger.info(f"Deleted {deleted_counts['deleted_leads']} leads")
            
            # Delete all reports
            logger.info("Deleting all reports...")
            result = self.supabase.table('reports').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            deleted_counts["deleted_reports"] = len(result.data) if result.data else 0
            logger.info(f"Deleted {deleted_counts['deleted_reports']} reports")
            
            # Delete all report_links
            logger.info("Deleting all report_links...")
            result = self.supabase.table('report_links').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            deleted_counts["deleted_report_links"] = len(result.data) if result.data else 0
            logger.info(f"Deleted {deleted_counts['deleted_report_links']} report_links")
            
            # Delete all assets
            logger.info("Deleting all assets...")
            result = self.supabase.table('assets').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            deleted_counts["deleted_assets"] = len(result.data) if result.data else 0
            logger.info(f"Deleted {deleted_counts['deleted_assets']} assets")
            
            # Clear storage buckets - delete ALL files in screenshots/ and reports/
            logger.info("Clearing storage buckets...")
            bucket_name = os.getenv("SUPABASE_BUCKET", "assets")
            
            folders_to_clear = ["screenshots", "reports"]
            total_deleted_files = 0
            
            for folder in folders_to_clear:
                try:
                    logger.info(f"Clearing {folder}/...")
                    
                    # Keep deleting until no more files found
                    # (Supabase .list() returns max 100 items, so we need to loop)
                    while True:
                        # List files in folder (max 100 per call)
                        files = self.supabase.storage.from_(bucket_name).list(folder, {
                            "limit": 1000,  # Try to get more items per call
                            "offset": 0
                        })
                        
                        if not files or len(files) == 0:
                            logger.info(f"No more files in {folder}/")
                            break
                        
                        # Create list of file paths to delete
                        file_paths = [f"{folder}/{file['name']}" for file in files if 'name' in file]
                        
                        if not file_paths:
                            logger.info(f"No more files in {folder}/")
                            break
                        
                        logger.info(f"Found {len(file_paths)} files in {folder}/, deleting...")
                        
                        # Delete files in batches of 100 (Supabase limit for delete)
                        batch_size = 100
                        for i in range(0, len(file_paths), batch_size):
                            batch = file_paths[i:i + batch_size]
                            try:
                                self.supabase.storage.from_(bucket_name).remove(batch)
                                total_deleted_files += len(batch)
                                logger.info(f"Deleted batch of {len(batch)} files (total: {total_deleted_files})")
                            except Exception as e:
                                logger.warning(f"Failed to delete batch: {e}")
                                continue
                        
                        # If we got less than limit, we're done
                        if len(files) < 100:
                            logger.info(f"Finished clearing {folder}/")
                            break
                        
                except Exception as e:
                    logger.warning(f"Failed to clear {folder}/: {e}")
                    continue
            
            deleted_counts["deleted_files"] = total_deleted_files
            logger.info(f"Total files deleted from storage: {total_deleted_files}")
            
            logger.info("All data cleared from Supabase successfully")
            return deleted_counts
            
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")
            raise


# Global instance
bulk_import_service = BulkImportService()
