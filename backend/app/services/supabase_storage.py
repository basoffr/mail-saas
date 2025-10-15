import os
from typing import Optional
from datetime import datetime, timedelta
from supabase import create_client, Client
from loguru import logger


class SupabaseStorage:
    """
    Supabase Storage service for generating signed URLs
    """
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "assets")
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials not configured, using mock URLs")
            self.client = None
        else:
            self.client: Client = create_client(self.url, self.key)
    
    def get_signed_url(self, image_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate signed URL for image_key.
        
        FIX: Removed double 'screenshots/' prefix issue.
        Key is now used EXACTLY as provided - no extra prefixing.
        
        Args:
            image_key: The image key - can be:
                     - Full path: "screenshots/filename.png" (used as-is)
                     - Just filename: "filename.png" (screenshots/ prefix added)
            expires_in: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Signed URL or None if not found
        """
        if not self.client:
            # Mock URL for development
            return f"https://via.placeholder.com/200x200?text={image_key}"
        
        try:
            paths_to_try = []
            
            # FIX: Check if key already contains 'screenshots/' prefix
            if image_key.startswith('screenshots/'):
                # Key already has full path - use as-is
                paths_to_try.append(image_key)
                logger.debug(f"Using key as-is (already has screenshots/ prefix): {image_key}")
            elif any(image_key.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                # Key is just filename - add screenshots/ prefix
                paths_to_try.append(f"screenshots/{image_key}")
                logger.debug(f"Adding screenshots/ prefix to: {image_key}")
            else:
                # Key has no extension - try different extensions
                extensions = ['.png', '.jpg', '.jpeg', '.webp']
                for ext in extensions:
                    paths_to_try.append(f"screenshots/{image_key}{ext}")
            
            for file_path in paths_to_try:
                try:
                    # Check if file exists and get signed URL
                    response = self.client.storage.from_(self.bucket_name).create_signed_url(
                        file_path, 
                        expires_in
                    )
                    
                    if response and 'signedURL' in response:
                        logger.info(f"✅ Generated signed URL for: {file_path}")
                        return response['signedURL']
                        
                except Exception as e:
                    logger.debug(f"File not found: {file_path} - {e}")
                    continue
            
            logger.warning(f"❌ No image found for key: {image_key} | Tried paths: {paths_to_try}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating signed URL for {image_key}: {e}")
            return None
    
    def get_signed_url_for_report(self, report_filename: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate signed URL for PDF report in 'reports' bucket.
        
        Uses fuzzy matching to handle filename variations:
        - Dots vs underscores: "domain.com" vs "domain_com"
        - Path variations: "domain_report.pdf" vs "domain_collections_page_report.pdf"
        
        Args:
            report_filename: The PDF filename (e.g., "solangefashion.com_report.pdf")
            expires_in: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Signed URL or None if not found
        """
        if not self.client:
            # Mock URL for development
            return f"https://via.placeholder.com/200x200?text={report_filename}"
        
        try:
            # Reports are stored in 'reports' bucket
            reports_bucket = "reports"
            
            # Normalize filename: replace dots with underscores
            # "angelicroots.com_report.pdf" -> "angelicroots_com_report.pdf"
            normalized_filename = report_filename.replace('.com_', '_com_').replace('.nl_', '_nl_')
            
            # Try exact match first
            paths_to_try = [
                report_filename,  # Original filename
                normalized_filename  # Normalized version
            ]
            
            for file_path in paths_to_try:
                try:
                    response = self.client.storage.from_(reports_bucket).create_signed_url(
                        file_path,
                        expires_in
                    )
                    
                    if response and 'signedURL' in response:
                        logger.info(f"✅ Generated signed URL for report: {file_path}")
                        return response['signedURL']
                        
                except Exception as e:
                    logger.debug(f"Report not found: {file_path} - {e}")
                    continue
            
            # If exact match fails, try fuzzy search by listing bucket
            # This handles cases like "domain_com_report.pdf" vs "domain_com_collections_page_report.pdf"
            try:
                # Extract base domain from filename
                # "angelicroots.com_report.pdf" -> "angelicroots"
                base_name = report_filename.split('_')[0].replace('.com', '').replace('.nl', '')
                
                # List all files in bucket
                files = self.client.storage.from_(reports_bucket).list()
                
                # Find files that start with the base domain name
                matching_files = [
                    f['name'] for f in files 
                    if f['name'].startswith(base_name) and f['name'].endswith('_report.pdf')
                ]
                
                if matching_files:
                    # Try the first matching file
                    matched_file = matching_files[0]
                    response = self.client.storage.from_(reports_bucket).create_signed_url(
                        matched_file,
                        expires_in
                    )
                    
                    if response and 'signedURL' in response:
                        logger.info(f"✅ Generated signed URL for report (fuzzy match): {matched_file}")
                        return response['signedURL']
                        
            except Exception as e:
                logger.debug(f"Fuzzy search failed: {e}")
            
            logger.warning(f"❌ No report found for: {report_filename} (tried: {paths_to_try})")
            return None
                
        except Exception as e:
            logger.error(f"Error generating signed URL for report {report_filename}: {e}")
            return None
    
    def list_images(self, prefix: str = "images/") -> list[str]:
        """List all images in the bucket"""
        if not self.client:
            return []
        
        try:
            response = self.client.storage.from_(self.bucket_name).list(prefix)
            return [item['name'] for item in response if item.get('name')]
        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return []


# Global instance
supabase_storage = SupabaseStorage()
