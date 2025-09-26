from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Column, Text
from sqlalchemy import JSON


class ReportType(str, Enum):
    pdf = "pdf"
    xlsx = "xlsx"
    png = "png"
    jpg = "jpg"
    jpeg = "jpeg"


class Report(SQLModel, table=True):
    """Report model for storing uploaded files metadata."""
    __tablename__ = "reports"
    
    id: str = Field(primary_key=True)
    filename: str = Field(index=True)
    type: ReportType = Field(index=True)
    size_bytes: int
    storage_path: str
    checksum: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: Optional[str] = None  # User ID from JWT
    
    # Optional metadata
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class ReportLink(SQLModel, table=True):
    """Link table for connecting reports to leads or campaigns."""
    __tablename__ = "report_links"
    
    id: str = Field(primary_key=True)
    report_id: str = Field(foreign_key="reports.id", index=True)
    lead_id: Optional[str] = Field(default=None, foreign_key="leads.id", index=True)
    campaign_id: Optional[str] = Field(default=None, foreign_key="campaigns.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Constraint: either lead_id or campaign_id must be set, but not both in MVP
    # This will be enforced at the service layer
