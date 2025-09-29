from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlmodel import SQLModel, Field, Column, JSON, Text
from sqlalchemy import DateTime, String, Integer, ForeignKey


class CampaignStatus(str, Enum):
    draft = "draft"
    running = "running"
    paused = "paused"
    completed = "completed"
    stopped = "stopped"


class MessageStatus(str, Enum):
    queued = "queued"
    sent = "sent"
    bounced = "bounced"
    opened = "opened"
    failed = "failed"
    canceled = "canceled"


class MessageEventType(str, Enum):
    sent = "sent"
    opened = "opened"
    bounced = "bounced"
    failed = "failed"


class Campaign(SQLModel, table=True):
    __tablename__ = "campaigns"
    __table_args__ = {'extend_existing': True}
    
    id: str = Field(primary_key=True)
    name: str = Field(sa_column=Column(Text, index=True))
    template_id: str = Field(sa_column=Column(String, ForeignKey("templates.id")))
    domain: Optional[str] = Field(default=None, sa_column=Column(String, index=True))  # Optional for backward compatibility
    start_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    status: CampaignStatus = Field(default=CampaignStatus.draft, sa_column=Column(String, index=True))
    
    # Follow-up settings
    followup_enabled: bool = Field(default=True)
    followup_days: int = Field(default=3)
    followup_attach_report: bool = Field(default=False)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))


class CampaignAudience(SQLModel, table=True):
    __tablename__ = "campaign_audience"
    __table_args__ = {'extend_existing': True}
    
    id: str = Field(primary_key=True)
    campaign_id: str = Field(sa_column=Column(String, ForeignKey("campaigns.id"), index=True))
    lead_ids: List[str] = Field(sa_column=Column(JSON))
    
    # Dedupe settings snapshot
    exclude_suppressed: bool = Field(default=True)
    exclude_recent_days: int = Field(default=14)
    one_per_domain: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    __table_args__ = {'extend_existing': True}
    
    id: str = Field(primary_key=True)
    campaign_id: str = Field(sa_column=Column(String, ForeignKey("campaigns.id"), index=True))
    lead_id: str = Field(sa_column=Column(String, ForeignKey("leads.id"), index=True))
    
    # Scheduling
    domain_used: str = Field(sa_column=Column(String, index=True))
    scheduled_at: datetime = Field(sa_column=Column(DateTime(timezone=True), index=True))
    sent_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    
    # Flow-based fields (optional for backward compatibility)
    mail_number: int = Field(default=1, sa_column=Column(Integer, index=True))  # 1-4 in flow
    alias: str = Field(default="christian", sa_column=Column(String))  # christian or victor
    from_email: Optional[str] = Field(default=None, sa_column=Column(String))
    reply_to_email: Optional[str] = Field(default=None, sa_column=Column(String))
    
    # Status tracking
    status: MessageStatus = Field(default=MessageStatus.queued, sa_column=Column(String, index=True))
    last_error: Optional[str] = Field(sa_column=Column(Text))
    open_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    
    # Follow-up relationship
    parent_message_id: Optional[str] = Field(sa_column=Column(String, ForeignKey("messages.id")))
    is_followup: bool = Field(default=False)
    
    # Retry tracking
    retry_count: int = Field(default=0)
    
    # SMTP tracking for inbox linking
    smtp_message_id: Optional[str] = Field(default=None, sa_column=Column(String, unique=True, index=True))
    x_campaign_message_id: Optional[str] = Field(default=None, sa_column=Column(String, index=True))
    
    # Asset logging (implementation plan requirement)
    with_image: bool = Field(default=False)
    with_report: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))


class MessageEvent(SQLModel, table=True):
    __tablename__ = "message_events"
    __table_args__ = {'extend_existing': True}
    
    id: str = Field(primary_key=True)
    message_id: str = Field(sa_column=Column(String, ForeignKey("messages.id"), index=True))
    event_type: MessageEventType = Field(sa_column=Column(String, index=True))
    
    # Event metadata
    meta: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON))
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
