from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class LeadStatus(str, Enum):
    active = "active"
    suppressed = "suppressed"
    bounced = "bounced"


class LeadOut(BaseModel):
    id: str
    email: str
    company: Optional[str] = None
    url: Optional[str] = None
    domain: Optional[str] = None
    status: LeadStatus = LeadStatus.active
    tags: List[str] = Field(default_factory=list)
    image_key: Optional[str] = None
    list_name: Optional[str] = None
    last_emailed_at: Optional[datetime] = None
    last_open_at: Optional[datetime] = None
    vars: Dict[str, Any] = Field(default_factory=dict)
    stopped: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Enriched fields (computed)
    has_report: bool = False
    has_image: bool = False
    vars_completeness: Optional[Dict[str, Any]] = None
    is_complete: bool = False
    is_deleted: bool = False


class LeadDetail(LeadOut):
    pass  # vars is now inherited from LeadOut


class LeadsListResponse(BaseModel):
    items: List[LeadOut]
    total: int


class LeadDeleteRequest(BaseModel):
    """Request to soft delete lead(s)."""
    lead_ids: List[str] = Field(..., min_length=1, max_length=100)
    reason: Optional[str] = None


class LeadDeleteResponse(BaseModel):
    """Response after soft delete operation."""
    deleted_count: int
    deleted_ids: List[str]
    failed_ids: List[str] = Field(default_factory=list)


class LeadRestoreResponse(BaseModel):
    """Response after restore operation."""
    restored_count: int
    restored_ids: List[str]
    failed_ids: List[str] = Field(default_factory=list)
