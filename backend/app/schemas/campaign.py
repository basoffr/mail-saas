from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.campaign import CampaignStatus, MessageStatus, MessageEventType


# Base campaign schemas
class CampaignOut(BaseModel):
    id: str
    name: str
    template_id: Optional[str] = Field(None, alias='templateId')  # Nullable - templates handled per message
    domain: str
    start_at: Optional[datetime] = Field(None, alias='startDate')  # V2.2: camelCase for frontend
    status: CampaignStatus
    followup_enabled: bool = Field(alias='followupEnabled')
    followup_days: int = Field(alias='followupDays')
    followup_attach_report: bool = Field(alias='followupAttachReport')
    created_at: datetime = Field(alias='createdAt')
    updated_at: datetime = Field(alias='updatedAt')
    
    # Count fields for UI display (computed from messages)
    target_count: int = Field(0, alias='targetCount')
    sent_count: int = Field(0, alias='sentCount')
    open_count: int = Field(0, alias='openCount')
    click_count: int = Field(0, alias='clickCount')
    bounce_count: int = Field(0, alias='bounceCount')
    reply_count: int = Field(0, alias='replyCount')
    
    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase
        by_alias = True  # Serialize using aliases (camelCase)


class MessageOut(BaseModel):
    id: str
    campaign_id: str
    lead_id: str
    domain_used: str
    scheduled_at: datetime
    sent_at: Optional[datetime]
    status: MessageStatus
    last_error: Optional[str]
    open_at: Optional[datetime]
    is_followup: bool
    retry_count: int


class MessageEventOut(BaseModel):
    id: str
    message_id: str
    event_type: MessageEventType
    meta: Optional[Dict[str, Any]]
    created_at: datetime


# Campaign creation payload
class AudienceFilter(BaseModel):
    status: Optional[List[str]] = None
    domain_tld: Optional[List[str]] = None
    has_image: Optional[bool] = None
    has_var: Optional[bool] = None
    last_emailed_before: Optional[datetime] = None


class AudienceSelection(BaseModel):
    mode: str = Field(..., description="'filter' or 'static'")
    filter_criteria: Optional[AudienceFilter] = None
    lead_ids: Optional[List[str]] = None
    
    # Dedupe settings
    exclude_suppressed: bool = True
    exclude_recent_days: int = 14
    one_per_domain: bool = False


class ScheduleSettings(BaseModel):
    start_mode: str = Field(..., description="'now' or 'scheduled'")
    start_at: Optional[datetime] = None


class FollowupSettings(BaseModel):
    enabled: bool = True
    days: int = 3
    attach_report: bool = False


class CampaignCreatePayload(BaseModel):
    """Simplified campaign creation payload.
    
    All settings are auto-assigned by backend:
    - Flow/version (round-robin first available domain)
    - Domain (1-to-1 with flow)
    - Templates (4 templates per flow version)
    - Followup (hard-coded: +3 workdays)
    - Throttle/window (hard-coded sending policy)
    """
    name: str = Field(..., min_length=1, max_length=255)
    audience: AudienceSelection
    schedule: ScheduleSettings
    
    # Legacy fields (deprecated, kept for backward compatibility)
    template_id: Optional[str] = None  # Ignored, auto-assigned
    domains: Optional[List[str]] = None  # Ignored, auto-assigned
    followup: Optional[FollowupSettings] = None  # Ignored, hard-coded


# Campaign detail with KPIs
class CampaignKPIs(BaseModel):
    total_planned: int
    total_sent: int
    total_opened: int
    total_failed: int
    open_rate: float
    avg_tempo_per_hour: float


class TimelinePoint(BaseModel):
    date: str  # YYYY-MM-DD format
    sent: int
    opened: int


class CampaignDetail(CampaignOut):
    kpis: CampaignKPIs
    timeline: List[TimelinePoint]
    domains_used: List[str]
    audience_count: int
    
    # Auto-assigned info (for UI display)
    flow_version: int
    templates: List[str]  # e.g., ["v1m1", "v1m2", "v1m3", "v1m4"]
    estimated_duration_days: int  # 9 workdays


# API response wrappers
class CampaignsResponse(BaseModel):
    items: List[CampaignOut]
    total: int


class MessagesResponse(BaseModel):
    items: List[MessageOut]
    total: int


# Action payloads
class CampaignActionResponse(BaseModel):
    ok: bool
    message: str


class DryRunDay(BaseModel):
    date: str  # YYYY-MM-DD
    planned: int


class DryRunResponse(BaseModel):
    by_day: List[DryRunDay]
    total_planned: int
    estimated_completion: Optional[datetime]


class ResendPayload(BaseModel):
    reason: Optional[str] = None


# Campaign queries
class CampaignQuery(BaseModel):
    page: int = 1
    page_size: int = 25
    status: Optional[List[CampaignStatus]] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class MessageQuery(BaseModel):
    page: int = 1
    page_size: int = 50
    campaign_id: Optional[str] = None
    status: Optional[List[MessageStatus]] = None
    lead_id: Optional[str] = None


# V2.2: Campaign Controls
class CampaignControlResponse(BaseModel):
    """Generic response for delete/pause/resume actions."""
    ok: bool = True
    message: Optional[str] = None


class StopLeadRequest(BaseModel):
    """Request to stop a lead's campaign flow."""
    reason: str = Field(..., description="unsubscribe | bounce | manual")


class StopLeadResponse(BaseModel):
    """Response after stopping a lead."""
    ok: bool = True
    lead_id: str
    canceled_count: int = 0
    reason: str


# V2.2: Scheduling View
class ScheduledMessageOut(BaseModel):
    """Simplified message for scheduling timeline."""
    message_id: str
    lead_id: str
    mail_number: int
    alias: str
    domain_used: str
    scheduled_at: datetime
    status: MessageStatus
    cancel_reason: Optional[str] = None


class ScheduleResponse(BaseModel):
    """Schedule view response."""
    campaign_id: str
    effective_start: datetime
    window: str = "08:00-17:00"
    streams: Dict[str, List[int]] = Field(default_factory=lambda: {
        "A": [0, 20, 40],
        "B": [10, 30, 50]
    })
    slots: List[ScheduledMessageOut]
    total_count: int
