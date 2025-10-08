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
    
    FIX: Removed double 'screenshots/' prefix issue.
    - Key is used EXACTLY as provided (no modifications)
    - No file existence check (avoids folder parsing issues)
    - Simple public URL generation for public buckets
    - Bucket 'assets' is public, so direct URLs work
    
    Args:
        key: Storage path EXACTLY as in database (e.g., 'screenshots/www_nttb_nl_webshop_.png')
    
    Returns:
        Public URL to the image
    
    Example:
        Input:  key='screenshots/www_nttb_nl_webshop_.png'
        Output: 'https://xxx.supabase.co/storage/v1/object/public/assets/screenshots/www_nttb_nl_webshop_.png'
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        bucket_name = "assets"  # Screenshots are in 'assets' bucket
        
        if not supabase_url:
            logger.error("SUPABASE_URL environment variable missing")
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        # FIX: Use key EXACTLY as provided - no parsing, no modifications
        # Generate public URL for assets bucket (which is public)
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{key}"
        
        logger.info(f"✅ Generated image URL | key: {key} | url: {public_url}")
        return public_url
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate image URL | key: {key} | error: {e}")
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
