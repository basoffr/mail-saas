import hashlib
import zipfile
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException
from app.models.report import ReportType
from app.schemas.report import BulkMapRow, BulkUploadResult


class FileHandler:
    """Handle file uploads, validation, and bulk processing."""
    
    ALLOWED_TYPES = {
        "application/pdf": ReportType.pdf,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ReportType.xlsx,
        "image/png": ReportType.png,
        "image/jpeg": ReportType.jpg,
        "image/jpg": ReportType.jpg
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_BULK_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_BULK_FILES = 100
    
    def __init__(self):
        self.storage_path = "reports/"  # In production: Supabase storage
    
    def validate_file(self, file: UploadFile) -> ReportType:
        """Validate uploaded file and return type."""
        if not file.content_type or file.content_type not in self.ALLOWED_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type. Allowed: {list(self.ALLOWED_TYPES.keys())}"
            )
        
        # Check file size (approximate)
        if hasattr(file, 'size') and file.size and file.size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=422,
                detail=f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        return self.ALLOWED_TYPES[file.content_type]
    
    async def save_file(self, file: UploadFile, report_id: str) -> Tuple[str, str, int]:
        """Save file and return (storage_path, checksum, size)."""
        # Read file content
        content = await file.read()
        
        # Validate size
        if len(content) > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=422,
                detail=f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Calculate checksum
        checksum = hashlib.md5(content).hexdigest()
        
        # Generate storage path
        file_extension = self._get_file_extension(file.filename or "file")
        storage_path = f"{self.storage_path}{report_id}{file_extension}"
        
        # In MVP: simulate file storage (in production: save to Supabase)
        # For now, we just return the path without actually saving
        
        return storage_path, checksum, len(content)
    
    def generate_download_url(self, storage_path: str) -> str:
        """Generate signed download URL (MVP: mock implementation)."""
        # In production: generate Supabase signed URL with 5min TTL
        # For MVP: return mock URL
        return f"https://storage.example.com/{storage_path}?expires={int((datetime.utcnow() + timedelta(minutes=5)).timestamp())}"
    
    async def process_bulk_upload(self, zip_file: UploadFile, mode: str, 
                                leads_data: List[Dict] = None) -> BulkUploadResult:
        """Process bulk ZIP upload with mapping."""
        # Validate ZIP file
        if not zip_file.content_type or "zip" not in zip_file.content_type:
            raise HTTPException(status_code=422, detail="File must be a ZIP archive")
        
        # Read ZIP content
        zip_content = await zip_file.read()
        
        if len(zip_content) > self.MAX_BULK_SIZE:
            raise HTTPException(
                status_code=422,
                detail=f"ZIP file too large. Maximum size: {self.MAX_BULK_SIZE // (1024*1024)}MB"
            )
        
        # Process ZIP
        mappings = []
        uploaded = 0
        failed = 0
        
        try:
            # Save ZIP to temporary location for processing (Windows compatible)
            import tempfile
            temp_zip_path = tempfile.mktemp(suffix=".zip")
            with open(temp_zip_path, "wb") as f:
                f.write(zip_content)
            
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                if len(file_list) > self.MAX_BULK_FILES:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Too many files in ZIP. Maximum: {self.MAX_BULK_FILES}"
                    )
                
                for file_name in file_list:
                    if file_name.endswith('/'):  # Skip directories
                        continue
                    
                    try:
                        # Extract file info
                        file_info = zip_ref.getinfo(file_name)
                        
                        if file_info.file_size > self.MAX_FILE_SIZE:
                            mappings.append({
                                "fileName": file_name,
                                "status": "failed",
                                "error": "File too large"
                            })
                            failed += 1
                            continue
                        
                        # Validate file type
                        file_type = self._detect_file_type(file_name)
                        if not file_type:
                            mappings.append({
                                "fileName": file_name,
                                "status": "failed", 
                                "error": "Unsupported file type"
                            })
                            failed += 1
                            continue
                        
                        # Perform mapping based on mode
                        mapping_result = self._map_file(file_name, mode, leads_data)
                        
                        if mapping_result["status"] == "matched":
                            # In production: actually save the file
                            mappings.append({
                                "fileName": file_name,
                                "to": mapping_result.get("target"),
                                "status": "ok"
                            })
                            uploaded += 1
                        else:
                            mappings.append({
                                "fileName": file_name,
                                "status": "failed",
                                "error": mapping_result.get("reason", "No match found")
                            })
                            failed += 1
                    
                    except Exception as e:
                        mappings.append({
                            "fileName": file_name,
                            "status": "failed",
                            "error": str(e)
                        })
                        failed += 1
            
            # Cleanup temp file
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
        
        except zipfile.BadZipFile:
            raise HTTPException(status_code=422, detail="Invalid ZIP file")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing ZIP: {str(e)}")
        
        return BulkUploadResult(
            total=len(file_list),
            uploaded=uploaded,
            failed=failed,
            mappings=mappings
        )
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return ''
    
    def _detect_file_type(self, filename: str) -> Optional[ReportType]:
        """Detect file type from filename."""
        extension = self._get_file_extension(filename).lower()
        
        type_map = {
            '.pdf': ReportType.pdf,
            '.xlsx': ReportType.xlsx,
            '.png': ReportType.png,
            '.jpg': ReportType.jpg,
            '.jpeg': ReportType.jpg
        }
        
        return type_map.get(extension)
    
    def _map_file(self, file_name: str, mode: str, leads_data: List[Dict] = None) -> Dict[str, Any]:
        """Map file to lead/campaign based on mode."""
        base_name = os.path.splitext(file_name)[0].lower()
        
        if mode == "by_image_key":
            # Match filename to lead image_key
            if leads_data:
                for lead in leads_data:
                    if lead.get("image_key", "").lower() == base_name:
                        return {
                            "status": "matched",
                            "target": {"kind": "lead", "id": lead["id"]}
                        }
            
            return {"status": "unmatched", "reason": "No matching image_key found"}
        
        elif mode == "by_email":
            # Match filename to lead email (before @ symbol)
            if leads_data:
                for lead in leads_data:
                    email = lead.get("email", "")
                    if email:
                        email_prefix = email.split("@")[0].lower()
                        if email_prefix == base_name:
                            return {
                                "status": "matched",
                                "target": {"kind": "lead", "id": lead["id"], "email": email}
                            }
            
            return {"status": "unmatched", "reason": "No matching email found"}
        
        return {"status": "unmatched", "reason": "Invalid mapping mode"}


# Global instance
file_handler = FileHandler()
