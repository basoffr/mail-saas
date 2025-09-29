import os
from datetime import datetime
from fastapi import APIRouter
from app.schemas.common import DataResponse
from app.services.supabase_storage import supabase_storage

router = APIRouter(tags=["health"])


@router.get("/health", response_model=DataResponse[dict])
async def health_check():
    """
    Health check endpoint for monitoring
    
    Returns:
        System health status including:
        - API status
        - Environment configuration
        - Storage connectivity
        - Timestamp
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": {
            "use_fixtures": os.getenv("USE_FIXTURES", "true").lower() == "true",
            "timezone": os.getenv("TZ", "UTC"),
            "supabase_configured": bool(os.getenv("SUPABASE_URL")),
        },
        "services": {
            "api": "ok",
            "storage": "ok" if supabase_storage.client else "mock",
        },
        "version": "1.0.0"
    }
    
    return {"data": health_data, "error": None}


@router.get("/health/detailed", response_model=DataResponse[dict])
async def detailed_health_check():
    """
    Detailed health check with service connectivity tests
    """
    checks = {
        "api": True,
        "storage": False,
        "environment": True
    }
    
    # Test Supabase Storage connectivity
    try:
        if supabase_storage.client:
            # Try to list images (basic connectivity test)
            images = supabase_storage.list_images()
            checks["storage"] = True
        else:
            checks["storage"] = "mock_mode"
    except Exception as e:
        checks["storage"] = f"error: {str(e)}"
    
    # Environment checks
    required_env_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"] if not os.getenv("USE_FIXTURES", "true").lower() == "true" else []
    missing_env = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_env:
        checks["environment"] = f"missing: {', '.join(missing_env)}"
    
    all_healthy = all(check is True for check in checks.values() if isinstance(check, bool))
    
    health_data = {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "uptime": "unknown",  # Could implement uptime tracking
        "memory_usage": "unknown"  # Could implement memory monitoring
    }
    
    return {"data": health_data, "error": None}
