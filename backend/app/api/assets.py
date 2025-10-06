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
    Get public URL for an image stored in Supabase Storage
    
    Args:
        key: Storage path (e.g., 'screenshots/labelnoir_40e03960.png')
    
    Returns:
        Public URL to the image
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        bucket_name = os.getenv("SUPABASE_BUCKET", "assets")
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Get public URL for the asset
        # Supabase Storage public URLs: {supabase_url}/storage/v1/object/public/{bucket}/{path}
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{key}"
        
        logger.info(f"Generated image URL for key: {key}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to get image URL for key {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get image URL: {str(e)}")


@router.get("/report-by-key", response_model=str)
async def get_report_url_by_key(key: str = Query(..., description="Storage key for report PDF")):
    """
    Get public URL for a report stored in Supabase Storage
    
    Args:
        key: Storage path (e.g., 'reports/labelnoir_report.pdf')
    
    Returns:
        Public URL to the report PDF
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        bucket_name = os.getenv("SUPABASE_BUCKET", "assets")
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Get public URL for the asset
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{key}"
        
        logger.info(f"Generated report URL for key: {key}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to get report URL for key {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report URL: {str(e)}")
