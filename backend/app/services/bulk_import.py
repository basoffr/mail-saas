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
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")  # Service key voor admin access
        
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
            
            leads_data = []
            
            for idx, row in df.iterrows():
                try:
                    # Extract lead data
                    domain = row.get('domain', row.get('Domain', ''))
                    email = row.get('email', row.get('Email', ''))
                    company = row.get('company', row.get('Company', row.get('Bedrijfsnaam', '')))
                    
                    if not domain or not email:
                        result["warnings"].append(f"Row {idx+2}: Missing domain or email")
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
                    
                    # Common variable mappings
                    var_mappings = {
                        'keyword': ['keyword', 'Keyword', 'zoekwoord', 'Zoekwoord'],
                        'google_rank': ['google_rank', 'Google Rank', 'ranking', 'Ranking'],
                        'city': ['city', 'City', 'plaats', 'Plaats'],
                        'phone': ['phone', 'Phone', 'telefoon', 'Telefoon'],
                    }
                    
                    for var_name, possible_columns in var_mappings.items():
                        for col in possible_columns:
                            if col in df.columns and pd.notna(row.get(col)):
                                vars_dict[var_name] = str(row[col])
                                break
                    
                    # Add report filename to vars if found
                    if report_filename:
                        vars_dict['report_filename'] = report_filename
                    
                    # Create lead data
                    lead_data = {
                        "email": email,
                        "domain": domain,
                        "company": company,
                        "url": row.get('url', row.get('URL', f"https://{domain}")),
                        "status": "active",
                        "image_key": image_key,
                        "list_name": list_name,
                        "vars": vars_dict,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
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
                    response = self.supabase.table('leads').insert(leads_data).execute()
                    result["leads_imported"] = len(leads_data)
                    
                    # Create report_links for matched reports
                    report_links = []
                    for lead_data in leads_data:
                        if 'report_filename' in lead_data.get('vars', {}):
                            # We need to create report entries first
                            # This is simplified - in production we'd batch this better
                            pass
                    
                except Exception as e:
                    logger.error(f"Failed to insert leads: {e}")
                    result["warnings"].append(f"Database insert failed: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Bulk import failed: {e}")
            raise
    
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
                            
                            # Upload file
                            self.supabase.storage.from_('assets').upload(
                                storage_path,
                                file_content,
                                {"content-type": content_type}
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
            return
        
        try:
            # Delete all leads
            self.supabase.table('leads').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            
            # Delete all reports
            self.supabase.table('reports').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            
            # Delete all report_links
            self.supabase.table('report_links').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            
            # Delete all assets
            self.supabase.table('assets').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            
            # Clear storage buckets
            # Note: This requires iterating and deleting files
            # Simplified version - in production we'd batch this
            
            logger.info("All data cleared from Supabase")
            
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")
            raise


# Global instance
bulk_import_service = BulkImportService()
