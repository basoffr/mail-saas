"""
Assets API - Endpoints voor Supabase Storage assets (screenshots, reports, etc.)
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from loguru import logger
import os
from supabase import create_client

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/image-by-key")
async def get_image_url_by_key(key: str = Query(..., description="Storage key (e.g., 'screenshots/example.png')")):
    """
    Redirect to image in Supabase Storage.
    
    FIX: Returns RedirectResponse instead of URL string.
    - Frontend <img> tags can now load images directly
    - Browser receives 307 redirect to actual image URL
    - Key is used EXACTLY as provided (no modifications)
    - Bucket 'assets' is public, so direct URLs work
    - Cache headers for better performance
    
    Args:
        key: Storage path EXACTLY as in database (e.g., 'screenshots/www_nttb_nl_webshop_.png')
    
    Returns:
        307 Temporary Redirect to the actual image
    
    Example:
        Input:  key='screenshots/www_nttb_nl_webshop_.png'
        Output: Redirect to 'https://xxx.supabase.co/storage/v1/object/public/assets/screenshots/www_nttb_nl_webshop_.png'
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
        
        logger.info(f"✅ Redirecting image | key: {key} → {public_url}")
        
        # Return redirect instead of URL string - this allows <img> tags to work!
        return RedirectResponse(
            url=public_url,
            status_code=307,  # Temporary redirect
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to redirect to image | key: {key} | error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get image: {str(e)}")


@router.get("/report-by-key")
async def get_report_url_by_key(key: str = Query(..., description="Storage key for report PDF")):
    """
    Redirect to report PDF in Supabase Storage.
    
    FIX: Returns RedirectResponse instead of URL string.
    - Frontend can now trigger direct downloads
    - Browser receives 307 redirect to actual PDF URL
    - Reports are in separate 'reports' bucket, not 'assets'
    
    Args:
        key: Filename only (e.g., 'labelnoir_report.pdf'), NOT full path
    
    Returns:
        307 Temporary Redirect to the actual PDF
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        bucket_name = "reports"  # Reports are in separate 'reports' bucket
        
        if not supabase_url:
            logger.error("SUPABASE_URL environment variable missing")
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        # Generate public URL
        # Reports are directly in bucket root (no subdirectory)
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{key}"
        
        logger.info(f"✅ Redirecting report | key: {key} → {public_url}")
        
        # Return redirect instead of URL string
        return RedirectResponse(
            url=public_url,
            status_code=307,  # Temporary redirect
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to redirect to report | key: {key} | error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")
