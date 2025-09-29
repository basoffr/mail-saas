from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class GlobalStats(BaseModel):
    total_sent: int
    total_opens: int
    open_rate: float
    bounces: int


class DomainStats(BaseModel):
    domain: str
    sent: int
    opens: int
    open_rate: float
    bounces: int
    last_activity: Optional[str] = None


class CampaignStats(BaseModel):
    id: str
    name: str
    sent: int
    opens: int
    open_rate: float
    bounces: int
    status: str
    start_date: Optional[str] = None


class TimelinePoint(BaseModel):
    date: str
    sent: int
    opens: int


class TimelineData(BaseModel):
    sent_by_day: List[TimelinePoint]
    opens_by_day: List[TimelinePoint]


class StatsSummary(BaseModel):
    global_stats: GlobalStats
    domains: List[DomainStats]
    campaigns: List[CampaignStats]
    timeline: TimelineData


class StatsQuery(BaseModel):
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    template_id: Optional[str] = None


class ExportQuery(BaseModel):
    scope: str  # global|domain|campaign
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    id: Optional[str] = None  # domain name or campaign_id for specific exports
