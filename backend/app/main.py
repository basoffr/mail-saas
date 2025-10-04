from fastapi import FastAPI, Request, HTTPException
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
    
    logger.error(
        f"Unhandled exception [trace:{trace_id}]: {str(exc)} - {request.method} {request.url}",
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

# Basic CORS (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(leads_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")
app.include_router(campaigns_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1/stats")
app.include_router(settings_router, prefix="/api/v1/settings")
app.include_router(inbox_router, prefix="/api/v1")
app.include_router(tracking_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
