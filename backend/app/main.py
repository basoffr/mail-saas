from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.leads import router as leads_router
from app.api.templates import router as templates_router
from app.api.campaigns import router as campaigns_router
from app.api.tracking import router as tracking_router
from app.api.reports import router as reports_router

app = FastAPI(title="Private Mail SaaS API", version="0.1.0")

# Basic CORS (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"data": {"ok": True}, "error": None}

app.include_router(leads_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")
app.include_router(campaigns_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(tracking_router, prefix="/api/v1")
