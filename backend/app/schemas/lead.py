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
    created_at: datetime
    updated_at: datetime
    
    # Enriched fields (computed)
    has_report: bool = False
    has_image: bool = False
    vars_completeness: Optional[Dict[str, Any]] = None
    is_complete: bool = False


class LeadDetail(LeadOut):
    pass  # vars is now inherited from LeadOut


class LeadsListResponse(BaseModel):
    items: List[LeadOut]
    total: int
