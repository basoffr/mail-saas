from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.models.report import ReportType


class ReportOut(BaseModel):
    """Report output for list view."""
    id: str
    filename: str
    type: ReportType
    size_bytes: int
    created_at: datetime
    bound_to: Optional[Dict[str, str]] = None  # {"kind": "lead|campaign", "id": "...", "label": "..."}


class ReportDetail(BaseModel):
    """Detailed report view."""
    id: str
    filename: str
    type: ReportType
    size_bytes: int
    storage_path: str
    checksum: Optional[str]
    created_at: datetime
    uploaded_by: Optional[str]
    meta: Optional[Dict[str, Any]]
    bound_to: Optional[Dict[str, str]] = None


class ReportsResponse(BaseModel):
    """Response for reports list."""
    items: List[ReportOut]
    total: int


class ReportsQuery(BaseModel):
    """Query parameters for reports list."""
    page: int = 1
    page_size: int = 25
    types: Optional[List[ReportType]] = None
    bound_filter: Optional[str] = None  # "all", "bound", "unbound"
    bound_kind: Optional[str] = None    # "lead", "campaign"
    bound_id: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class ReportUploadPayload(BaseModel):
    """Payload for single report upload."""
    lead_id: Optional[str] = None
    campaign_id: Optional[str] = None


class BulkMapRow(BaseModel):
    """Single row in bulk mapping result."""
    file_name: str
    base_key: str
    target: Optional[Dict[str, str]] = None  # {"kind": "lead|campaign", "id": "...", "email": "..."}
    status: str  # "matched", "unmatched", "ambiguous"
    reason: Optional[str] = None


class BulkUploadResult(BaseModel):
    """Result of bulk upload operation."""
    total: int
    uploaded: int
    failed: int
    mappings: List[Dict[str, Any]]


class ReportBindPayload(BaseModel):
    """Payload for binding report to entity."""
    report_id: str
    lead_id: Optional[str] = None
    campaign_id: Optional[str] = None


class ReportUnbindPayload(BaseModel):
    """Payload for unbinding report."""
    report_id: str


class DownloadResponse(BaseModel):
    """Response for download request."""
    url: str
    expires_at: datetime
