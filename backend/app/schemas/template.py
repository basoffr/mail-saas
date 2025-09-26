from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr


class TemplateOut(BaseModel):
    """Basic template info for list view"""
    id: str
    name: str
    subject_template: str
    updated_at: datetime
    required_vars: List[str]


class TemplateAssetOut(BaseModel):
    """Template asset info"""
    key: str
    type: str  # 'static' | 'cid'


class TemplateVarItem(BaseModel):
    """Template variable info"""
    key: str
    required: bool
    source: str  # 'lead' | 'vars' | 'campaign' | 'image'
    example: Optional[str] = None


class TemplateDetail(BaseModel):
    """Detailed template info"""
    id: str
    name: str
    subject_template: str
    body_template: str
    updated_at: datetime
    required_vars: List[str]
    assets: Optional[List[TemplateAssetOut]] = None
    variables: Optional[List[TemplateVarItem]] = None


class TemplatePreviewResponse(BaseModel):
    """Template preview result"""
    html: str
    text: str
    warnings: Optional[List[str]] = None


class TestsendPayload(BaseModel):
    """Testsend request payload"""
    to: EmailStr
    leadId: Optional[str] = None


class TemplatesResponse(BaseModel):
    """Templates list response"""
    items: List[TemplateOut]
    total: Optional[int] = None
