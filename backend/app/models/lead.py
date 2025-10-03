from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import DateTime
from enum import Enum


class LeadStatus(str, Enum):
    active = "active"
    suppressed = "suppressed"
    bounced = "bounced"


class Lead(SQLModel, table=True):
    __tablename__ = "leads"
    __table_args__ = {'extend_existing': True}

    id: str = Field(primary_key=True)
    email: str = Field(index=True, unique=True)
    company: Optional[str] = None
    url: Optional[str] = None
    domain: Optional[str] = Field(default=None, index=True)
    status: LeadStatus = Field(default=LeadStatus.active)
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    image_key: Optional[str] = None
    list_name: Optional[str] = Field(default=None, index=True)
    last_emailed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), index=True))
    last_open_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    vars: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    stopped: bool = Field(default=False, index=True)
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), index=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))


class Asset(SQLModel, table=True):
    __tablename__ = "assets"
    __table_args__ = {'extend_existing': True}

    id: str = Field(primary_key=True)
    key: str = Field(index=True, unique=True)
    mime: str
    size: int
    checksum: Optional[str] = None
    storage_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))


class ImportJobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ImportJob(SQLModel, table=True):
    __tablename__ = "import_jobs"
    __table_args__ = {'extend_existing': True}

    id: str = Field(primary_key=True)
    filename: str
    status: ImportJobStatus = Field(default=ImportJobStatus.pending)
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
