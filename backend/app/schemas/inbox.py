from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from .common import DataResponse


class InboxMessageOut(BaseModel):
    id: str
    account_id: str
    account_label: str
    folder: str
    uid: int
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: Optional[List[str]] = None
    from_email: str
    from_name: Optional[str] = None
    to_email: Optional[str] = None
    subject: str
    snippet: str
    raw_size: Optional[int] = None
    received_at: datetime
    is_read: bool
    
    # Linking info
    linked_campaign_id: Optional[str] = None
    linked_campaign_name: Optional[str] = None
    linked_lead_id: Optional[str] = None
    linked_lead_email: Optional[str] = None
    linked_message_id: Optional[str] = None
    weak_link: bool = False
    encoding_issue: bool = False


class InboxListResponse(BaseModel):
    items: List[InboxMessageOut]
    total: int


class FetchStartResponse(BaseModel):
    ok: bool
    run_id: str


class MarkReadResponse(BaseModel):
    ok: bool


class MailAccountOut(BaseModel):
    id: str
    label: str
    imap_host: str
    imap_port: int
    use_ssl: bool
    username_masked: str  # Never show plain username
    active: bool
    last_fetch_at: Optional[datetime] = None
    last_seen_uid: Optional[int] = None


class MailAccountUpsert(BaseModel):
    label: str
    imap_host: str
    imap_port: int = 993
    use_ssl: bool = True
    username: str
    secret_ref: str  # Reference to secret store


class MailAccountTestResponse(BaseModel):
    ok: bool
    message: str


class InboxRunOut(BaseModel):
    id: str
    account_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    new_count: Optional[int] = None
    error: Optional[str] = None


class InboxQuery(BaseModel):
    page: int = 1
    page_size: int = 25
    account_id: Optional[str] = None
    campaign_id: Optional[str] = None
    unread: Optional[bool] = None
    q: Optional[str] = None  # Search query
    from_date: Optional[str] = None  # ISO date
    to_date: Optional[str] = None    # ISO date


# Response wrappers
InboxMessagesResponse = DataResponse[InboxListResponse]
FetchResponse = DataResponse[FetchStartResponse]
MarkReadResponseWrapped = DataResponse[MarkReadResponse]
MailAccountsResponse = DataResponse[List[MailAccountOut]]
MailAccountTestResponseWrapped = DataResponse[MailAccountTestResponse]
InboxRunsResponse = DataResponse[List[InboxRunOut]]
