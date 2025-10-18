import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import traceback

from app.api.leads import router as leads_router
from app.api.templates import router as templates_router
from app.api.campaigns import router as campaigns_router
from app.api.tracking import router as tracking_router
from app.api.reports import router as reports_router
from app.api.stats import router as stats_router
from app.api.settings import router as settings_router
from app.api.inbox import router as inbox_router
from app.api.exports import router as exports_router
from app.api.health import router as health_router
from app.api.bulk_import import router as bulk_import_router
from app.api.assets import router as assets_router
from app.api.admin import router as admin_router
from app.api.auth import router as auth_router

app = FastAPI(title="Private Mail SaaS API", version="0.1.0")


# Central Exception Handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent {data, error} format"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url}")
    
    # Extract error message from detail
    error_message = exc.detail
    if isinstance(exc.detail, dict):
        error_message = exc.detail.get("error", str(exc.detail))
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "error": error_message}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with consistent {data, error} format"""
    trace_id = id(exc)  # Simple trace ID
    
    # Avoid f-string formatting issues with error messages containing braces
    exc_str = str(exc).replace('{', '{{').replace('}', '}}')  # Escape braces for logger
    
    logger.error(
        f"Unhandled exception [trace:{trace_id}]: {exc_str} - {request.method} {request.url}",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "url": str(request.url),
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "data": None, 
            "error": f"Internal server error [trace:{trace_id}]"
        }
    )

# CORS configuration
# Support both CORS_ORIGINS (comma-separated) and FRONTEND_ORIGIN (single)
cors_origins = os.getenv("CORS_ORIGINS")
frontend_origin = os.getenv("FRONTEND_ORIGIN")

if cors_origins:
    # Multiple origins (comma-separated)
    allowed_origins = [origin.strip() for origin in cors_origins.split(",")]
    logger.info(f"✅ CORS restricted to: {allowed_origins}")
elif frontend_origin:
    # Single origin (backward compatibility)
    allowed_origins = [frontend_origin]
    logger.info(f"✅ CORS restricted to: {frontend_origin}")
else:
    # Fallback to allow all (development only)
    allowed_origins = ["*"]
    logger.warning("⚠️  CORS allowing all origins (set CORS_ORIGINS for production)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# Check if RBAC is enabled
use_rbac = os.getenv("USE_RBAC", "false").lower() == "true"

if use_rbac:
    logger.info("🔒 RBAC enabled - applying role-based access control")
    from app.security.rbac import require_role
    
    # Public routes (no auth)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(tracking_router, prefix="/api/v1")  # Open tracking needs public access
    app.include_router(assets_router, prefix="/api/v1")    # Public asset access
    
    # Auth routes (uses its own auth dependency)
    app.include_router(auth_router)
    
    # Read-only routes (admin + viewer)
    app.include_router(
        stats_router, 
        prefix="/api/v1/stats",
        dependencies=[Depends(require_role("admin", "viewer"))]
    )
    app.include_router(
        inbox_router, 
        prefix="/api/v1",
        dependencies=[Depends(require_role("admin", "viewer"))]
    )
    app.include_router(
        exports_router, 
        prefix="/api/v1/exports",
        dependencies=[Depends(require_role("admin", "viewer"))]
    )
    
    # Mutating routes (admin only)
    app.include_router(
        leads_router, 
        prefix="/api/v1",
        dependencies=[Depends(require_role("admin"))]
    )
    app.include_router(
        templates_router, 
        prefix="/api/v1",
        dependencies=[Depends(require_role("admin"))]
    )
    app.include_router(
        campaigns_router, 
        prefix="/api/v1",
        dependencies=[Depends(require_role("admin"))]
    )
    app.include_router(
        reports_router, 
        prefix="/api/v1",
        dependencies=[Depends(require_role("admin"))]
    )
    app.include_router(
        settings_router, 
        prefix="/api/v1/settings",
        dependencies=[Depends(require_role("admin"))]
    )
    app.include_router(
        bulk_import_router, 
        prefix="/api/v1",
        dependencies=[Depends(require_role("admin"))]
    )
    app.include_router(
        admin_router, 
        prefix="/api/v1/admin",
        dependencies=[Depends(require_role("admin"))]
    )
    
else:
    logger.warning("⚠️  RBAC disabled - all routes are open (set USE_RBAC=true for production)")
    
    # Include all routers without auth (legacy mode)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router)  # Still include for /me endpoint
    app.include_router(leads_router, prefix="/api/v1")
    app.include_router(templates_router, prefix="/api/v1")
    app.include_router(campaigns_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")
    app.include_router(stats_router, prefix="/api/v1/stats")
    app.include_router(settings_router, prefix="/api/v1/settings")
    app.include_router(inbox_router, prefix="/api/v1")
    app.include_router(tracking_router, prefix="/api/v1")
    app.include_router(exports_router, prefix="/api/v1/exports")
    app.include_router(bulk_import_router, prefix="/api/v1")
    app.include_router(assets_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1/admin")
