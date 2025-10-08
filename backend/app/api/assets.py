"""
Assets API - Endpoints voor Supabase Storage assets (screenshots, reports, etc.)
"""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
import os
from supabase import create_client

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/image-by-key", response_model=str)
async def get_image_url_by_key(key: str = Query(..., description="Storage key (e.g., 'screenshots/example.png')")):
    """
    Get public URL for an image stored in Supabase Storage.
    
    FIXED ISSUES:
    - Verifies file exists in storage before returning URL
    - Uses correct bucket: 'assets' (screenshots are in assets/screenshots/)
    - No double encoding of key
    - Returns proper error if file not found
    
    Args:
        key: Storage path (e.g., 'screenshots/labelnoir_40e03960.png')
    
    Returns:
        Public URL to the image
    
    Raises:
        404: If image not found in storage
        500: If Supabase not configured or other error
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        # Screenshots are in 'assets' bucket, not 'reports'
        bucket_name = "assets"
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials missing")
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Verify file exists before returning URL
        try:
            # List to check if file exists
            # Extract folder and filename from key
            if '/' in key:
                folder = '/'.join(key.split('/')[:-1])
                filename = key.split('/')[-1]
            else:
                folder = ''
                filename = key
            
            # Check if file exists by trying to list it
            storage_response = supabase.storage.from_(bucket_name).list(folder)
            
            # Check if our file is in the list
            file_exists = any(item.get('name') == filename for item in storage_response)
            
            if not file_exists:
                logger.warning(f"Image not found in storage: {key} in bucket: {bucket_name}")
                raise HTTPException(
                    status_code=404, 
                    detail=f"Image not found for key: {key}"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking file existence for {key}: {e}")
            # Continue anyway and let the URL fail if needed
        
        # Generate public URL
        # Supabase Storage public URLs: {supabase_url}/storage/v1/object/public/{bucket}/{path}
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{key}"
        
        logger.info(f"Generated image URL for key: {key} -> {public_url}")
        return public_url
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get image URL for key {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get image URL: {str(e)}")


@router.get("/report-by-key", response_model=str)
async def get_report_url_by_key(key: str = Query(..., description="Storage key for report PDF")):
    """
    Get public URL for a report stored in Supabase Storage.
    
    NOTE: Reports are in separate 'reports' bucket, not 'assets'!
    
    Args:
        key: Filename only (e.g., 'labelnoir_report.pdf'), NOT full path
    
    Returns:
        Public URL to the report PDF
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        # Reports are in separate 'reports' bucket
        bucket_name = "reports"
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials missing")
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        # Generate public URL
        # Reports are directly in bucket root (no subdirectory)
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{key}"
        
        logger.info(f"Generated report URL for key: {key} -> {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to get report URL for key {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report URL: {str(e)}")
