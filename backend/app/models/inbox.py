from datetime import datetime
from typing import Optional, List, Any
from sqlmodel import SQLModel, Field, Column, JSON
from enum import Enum


class MailAccount(SQLModel, table=True):
    __tablename__ = "mail_accounts"
    
    id: str = Field(primary_key=True)
    label: str = Field(index=True)
    imap_host: str
    imap_port: int = Field(default=993)
    use_ssl: bool = Field(default=True)
    username: str
    secret_ref: str  # Reference to secret store, never plain password
    active: bool = Field(default=True, index=True)
    last_fetch_at: Optional[datetime] = None
    last_seen_uid: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MailMessage(SQLModel, table=True):
    __tablename__ = "mail_messages"
    
    id: str = Field(primary_key=True)
    account_id: str = Field(foreign_key="mail_accounts.id", index=True)
    folder: str = Field(default='INBOX')
    uid: int
    message_id: Optional[str] = Field(default=None, index=True)
    in_reply_to: Optional[str] = Field(default=None, index=True)
    references: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    from_email: str = Field(index=True)
    from_name: Optional[str] = None
    to_email: Optional[str] = None
    subject: str
    snippet: str  # Max ~20kB
    raw_size: Optional[int] = None
    received_at: datetime = Field(index=True)
    is_read: bool = Field(default=False)
    
    # Linking fields
    linked_campaign_id: Optional[str] = Field(default=None, foreign_key="campaigns.id", index=True)
    linked_lead_id: Optional[str] = Field(default=None, foreign_key="leads.id", index=True)
    linked_message_id: Optional[str] = Field(default=None, foreign_key="messages.id", index=True)
    weak_link: bool = Field(default=False)
    encoding_issue: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MailFetchRun(SQLModel, table=True):
    __tablename__ = "mail_fetch_runs"
    
    id: str = Field(primary_key=True)
    account_id: str = Field(foreign_key="mail_accounts.id", index=True)
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    finished_at: Optional[datetime] = None
    new_count: Optional[int] = None
    error: Optional[str] = None
