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
async def get_image_url_by_key(
    key: str = Query(..., description="Storage key (e.g., 'screenshots/example.png')"),
    format: str = Query("redirect", description="Response format: 'redirect' or 'json'")
):
    """
    Get image from Supabase Storage.
    
    Args:
        key: Storage path EXACTLY as in database (e.g., 'screenshots/www_nttb_nl_webshop_.png')
        format: 'redirect' (default) for browser redirect, 'json' for API response with URL
    
    Returns:
        - format=redirect: 307 Temporary Redirect to the actual image
        - format=json: JSON object with {data: {url: "..."}, error: null}
    
    Example:
        /image-by-key?key=screenshots/test.png&format=redirect → Redirects to image
        /image-by-key?key=screenshots/test.png&format=json    → Returns JSON with URL
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        bucket_name = "assets"  # Screenshots are in 'assets' bucket
        
        if not supabase_url:
            logger.error("SUPABASE_URL environment variable missing")
            if format == "json":
                return {"data": None, "error": "Supabase not configured"}
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        # Generate public URL for assets bucket (which is public)
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{key}"
        
        logger.info(f"✅ Image URL generated | key: {key} | format: {format} → {public_url}")
        
        if format == "json":
            # Return JSON response for API clients
            return {"data": {"url": public_url}, "error": None}
        else:
            # Return redirect for browser/img tags
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
        logger.error(f"❌ Failed to get image | key: {key} | error: {e}")
        if format == "json":
            return {"data": None, "error": f"Failed to get image: {str(e)}"}
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
