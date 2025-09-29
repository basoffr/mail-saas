from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.models.settings import DNSStatus, DomainConfig, DomainAlias


class SendingWindow(BaseModel):
    days: List[str]
    from_time: str = Field(alias="from")
    to: str
    
    class Config:
        populate_by_name = True


class ThrottleInfo(BaseModel):
    emails_per: int = Field(alias="emailsPer")
    minutes: int
    
    class Config:
        populate_by_name = True


class DomainAliasOut(BaseModel):
    """Frontend-compatible domain alias"""
    email: str
    name: str
    active: bool
    
    class Config:
        populate_by_name = True


class DomainConfigOut(BaseModel):
    """Frontend-compatible domain configuration"""
    domain: str
    display_name: str = Field(alias="displayName")
    smtp_host: str = Field(alias="smtpHost")
    smtp_port: int = Field(alias="smtpPort")
    use_tls: bool = Field(alias="useTls")
    aliases: List[DomainAliasOut]
    daily_limit: int = Field(alias="dailyLimit")
    throttle_minutes: int = Field(alias="throttleMinutes")
    dns_status: Dict[str, str] = Field(alias="dnsStatus")  # spf/dkim/dmarc status
    reputation_score: str = Field(alias="reputationScore")
    active: bool
    
    class Config:
        populate_by_name = True


class EmailInfra(BaseModel):
    current: str
    provider: str | None
    provider_enabled: bool = Field(alias="providerEnabled")
    dns: Dict[str, bool]
    
    class Config:
        populate_by_name = True


class SettingsOut(BaseModel):
    timezone: str
    window: SendingWindow
    throttle: ThrottleInfo
    domains: List[str]  # Simple list for backward compatibility
    domains_config: List[DomainConfigOut] = Field(alias="domainsConfig")  # Extended config
    unsubscribe_text: str = Field(alias="unsubscribeText")
    unsubscribe_url: str = Field(alias="unsubscribeUrl")
    tracking_pixel_enabled: bool = Field(alias="trackingPixelEnabled")
    email_infra: EmailInfra = Field(alias="emailInfra")

    class Config:
        populate_by_name = True


class SettingsUpdate(BaseModel):
    unsubscribe_text: str | None = Field(None, min_length=1, max_length=50, alias="unsubscribeText")
    tracking_pixel_enabled: bool | None = Field(None, alias="trackingPixelEnabled")

    class Config:
        populate_by_name = True

    @field_validator('unsubscribe_text')
    def validate_unsubscribe_text(cls, v):
        if v is not None and (len(v.strip()) < 1 or len(v.strip()) > 50):
            raise ValueError('Unsubscribe text must be between 1 and 50 characters')
        return v.strip() if v else v


class SettingsResponse(BaseModel):
    data: SettingsOut
    error: str | None = None
