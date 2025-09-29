from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
