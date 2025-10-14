"""
Simple Reports Store - Direct Supabase Storage Access
No database needed, just list files from storage bucket.
"""
import os
from typing import List, Optional, Tuple
from datetime import datetime
from supabase import create_client, Client
import logging

from app.schemas.report import ReportsQuery, ReportOut

logger = logging.getLogger(__name__)


class StorageReportsStore:
    """Simple reports store that reads directly from Supabase Storage."""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.bucket_name = 'reports'
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.warning("Supabase credentials not found, Storage reports disabled")
            return
        
        try:
            self.supabase = create_client(url, key)
            logger.info("✅ Storage-based ReportsStore initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase for reports: {e}")
    
    def _extract_domain_from_filename(self, filename: str) -> Optional[str]:
        """Extract domain from filename for search purposes."""
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Try to extract domain (first part before underscore)
        parts = name_without_ext.replace('-', '_').split('_')
        
        if parts:
            domain = parts[0]
            # Clean www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        
        return None
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type from extension."""
        ext = filename.lower().rsplit('.', 1)[-1]
        valid_types = ['pdf', 'xlsx', 'png', 'jpg', 'jpeg']
        return ext if ext in valid_types else 'pdf'
    
    def list_reports(self, query: ReportsQuery) -> Tuple[List[ReportOut], int]:
        """List reports directly from Storage bucket."""
        if not self.supabase:
            logger.warning("Supabase not initialized")
            return [], 0
        
        try:
            # Use Storage SDK to list files
            # Note: Supabase Python SDK .list() returns ALL files by default (no pagination needed)
            files = self.supabase.storage.from_(self.bucket_name).list()
            
            if not files:
                files = []
            
            logger.info(f"Storage SDK returned {len(files)} files")
            
            # Convert to ReportOut format
            reports = []
            for file_obj in files:
                try:
                    filename = file_obj.get('name', '')
                    
                    # Skip directories (if any)
                    if not filename or filename.endswith('/'):
                        continue
                    
                    # Extract file type from extension
                    file_type = self._get_file_type(filename)
                    
                    # Get size from metadata (Storage SDK structure)
                    # Ensure we always have an integer value
                    metadata = file_obj.get('metadata', {})
                    size_bytes = 0  # Default
                    if isinstance(metadata, dict):
                        size_val = metadata.get('size')
                        if size_val is not None:
                            try:
                                size_bytes = int(size_val)
                            except (ValueError, TypeError):
                                size_bytes = 0
                    
                    # Get timestamp - ensure we always have a string value
                    created_at = file_obj.get('created_at')
                    if not created_at or created_at is None:
                        created_at = file_obj.get('updated_at')
                    if not created_at or created_at is None:
                        created_at = datetime.utcnow().isoformat()
                    
                    # For bound_to, try to extract domain from filename
                    domain = self._extract_domain_from_filename(filename)
                    bound_to = None
                    if domain:
                        bound_to = {
                            "kind": "lead",
                            "id": domain,
                            "label": f"Domain: {domain}"
                        }
                    
                    # Create ReportOut object
                    report = ReportOut(
                        id=filename,  # Use filename as ID for Storage-based approach
                        filename=filename,
                        type=file_type,
                        size_bytes=size_bytes,
                        created_at=created_at,
                        bound_to=bound_to
                    )
                    
                    reports.append(report)
                except Exception as e:
                    logger.warning(f"Failed to process file {file_obj.get('name', 'unknown')}: {e}")
                    continue
            
            # Apply search filter
            if query.search:
                search_lower = query.search.lower()
                reports = [
                    r for r in reports 
                    if search_lower in r.filename.lower() or 
                       (r.bound_to and search_lower in r.bound_to.get('label', '').lower())
                ]
            
            # Apply type filter
            if query.types:
                reports = [r for r in reports if r.type in query.types]
            
            # Apply bound filter
            if query.bound_filter:
                if query.bound_filter == "bound":
                    reports = [r for r in reports if r.bound_to is not None]
                elif query.bound_filter == "unbound":
                    reports = [r for r in reports if r.bound_to is None]
            
            # Sort by filename
            reports.sort(key=lambda r: r.filename)
            
            total = len(reports)
            
            # Pagination
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            reports = reports[start:end]
            
            logger.info(f"Listed {len(reports)} reports from Storage (total: {total})")
            
            return reports, total
            
        except Exception as e:
            logger.error(f"Failed to list reports from Storage: {e}")
            return [], 0
    
    def get_download_url(self, filename: str, expires_in: int = 3600) -> str:
        """Get signed URL for downloading a file."""
        if not self.supabase:
            raise Exception("Supabase not initialized")
        
        try:
            # Create signed URL
            result = self.supabase.storage.from_(self.bucket_name).create_signed_url(
                filename, 
                expires_in
            )
            
            return result.get('signedURL') or result.get('signedUrl', '')
        except Exception as e:
            logger.error(f"Failed to create download URL for {filename}: {e}")
            raise
