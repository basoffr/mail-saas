from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.core.auth import require_auth
from app.schemas.lead import LeadOut, LeadDetail, LeadsListResponse, LeadStatus
from app.services.leads_store import LeadsStore
from app.services.leads_import import process_import_file
from app.services.template_preview import render_preview
from app.schemas.common import DataResponse
from app.services.import_jobs import import_job_store
from app.services.supabase_storage import supabase_storage
from app.services.lead_enrichment import enrich_leads_bulk, enrich_lead_with_metadata, get_lead_variables_detail

router = APIRouter(dependencies=[Depends(require_auth)])

# In-memory store for MVP
store = LeadsStore()



@router.get("/leads", response_model=DataResponse[LeadsListResponse])
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[List[LeadStatus]] = Query(default=None),
    domain_tld: Optional[List[str]] = Query(default=None),
    has_image: Optional[bool] = None,
    has_var: Optional[bool] = None,
    search: Optional[str] = None,
    list_name: Optional[str] = None,
    is_complete: Optional[bool] = None,
):
    items, total = store.query(
        page=page,
        page_size=page_size,
        status=status,
        domain_tld=domain_tld,
        has_image=has_image,
        has_var=has_var,
        search=search,
        list_name=list_name,
        is_complete=is_complete,
    )
    
    # Enrich leads with metadata (zonder full completeness voor performance)
    enriched_items = enrich_leads_bulk(items, include_completeness=True)
    
    return {"data": {"items": enriched_items, "total": total}, "error": None}


@router.get("/leads/{lead_id}", response_model=DataResponse[LeadDetail])
async def get_lead(lead_id: str):
    lead = store.get(lead_id)
    if not lead:
        return {"data": None, "error": "Not Found"}
    
    # Enrich with full metadata including completeness
    enriched_lead = enrich_lead_with_metadata(lead, include_completeness=True)
    
    return {"data": enriched_lead, "error": None}


@router.get("/leads/{lead_id}/variables")
async def get_lead_variables(lead_id: str):
    """Get detailed variables information for lead (for drawer view)."""
    lead = store.get(lead_id)
    if not lead:
        return {"data": None, "error": "Not Found"}
    
    variables_detail = get_lead_variables_detail(lead)
    
    return {"data": variables_detail, "error": None}


class ImportResult(BaseModel):
    inserted: int
    updated: int
    skipped: int
    jobId: str


@router.post("/import/leads", response_model=DataResponse[ImportResult])
async def import_leads(file: UploadFile = File(...)):
    result = await process_import_file(file, store)
    return {"data": result, "error": None}


class AssetUrl(BaseModel):
    url: str


@router.get("/assets/image-by-key", response_model=DataResponse[AssetUrl])
async def get_asset_url(key: str):
    """
    Get signed URL for image by key
    
    Args:
        key: Image key (e.g., "acme_picture")
    
    Returns:
        Signed URL with 1 hour expiration
    """
    signed_url = supabase_storage.get_signed_url(key, expires_in=3600)
    
    if not signed_url:
        return {"data": None, "error": f"Image not found for key: {key}"}
    
    return {"data": {"url": signed_url}, "error": None}


class PreviewRequest(BaseModel):
    template_id: str
    lead_id: str


class PreviewResponse(BaseModel):
    html: str
    text: str
    warnings: List[str] = []


@router.post("/previews/render", response_model=DataResponse[PreviewResponse])
async def previews_render(payload: PreviewRequest):
    # Extract mail number from template_id (e.g., v1m3 -> 3)
    import re
    mail_number = 1  # default
    match = re.search(r'm(\d)$', payload.template_id)
    if match:
        mail_number = int(match.group(1))
    
    preview = render_preview(payload.template_id, payload.lead_id, store, mail_number=mail_number)
    return {"data": preview, "error": None}


class ImportJobError(BaseModel):
    row: int
    field: str
    reason: str


class ImportJobOut(BaseModel):
    id: str
    filename: str
    status: str  # queued|running|succeeded|failed
    progress: float
    inserted: int
    updated: int
    skipped: int
    errors: List[ImportJobError]
    startedAt: datetime
    finishedAt: Optional[datetime] = None


@router.get("/import/jobs/{job_id}", response_model=DataResponse[ImportJobOut])
async def get_import_job(job_id: str):
    rec = import_job_store.get(job_id)
    if not rec:
        return {"data": None, "error": "Not Found"}
    # map dataclass to pydantic
    return {
        "data": {
            "id": rec.id,
            "filename": rec.filename,
            "status": rec.status,
            "progress": rec.progress,
            "inserted": rec.inserted,
            "updated": rec.updated,
            "skipped": rec.skipped,
            "errors": [{"row": e.row, "field": e.field, "reason": e.reason} for e in rec.errors],
            "startedAt": rec.startedAt,
            "finishedAt": rec.finishedAt,
        },
        "error": None,
    }


class LeadStopResponse(BaseModel):
    ok: bool
    lead_id: str
    stopped: bool
    canceled: int


@router.post("/leads/{lead_id}/stop", response_model=DataResponse[LeadStopResponse])
async def stop_lead(lead_id: str):
    """Stop all future emails to this lead."""
    lead = store.get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="lead_not_found")
    
    # Stop the lead
    canceled_count = store.stop_lead(lead_id)
    
    return {
        "data": {
            "ok": True,
            "lead_id": lead_id,
            "stopped": True,
            "canceled": canceled_count
        },
        "error": None
    }
