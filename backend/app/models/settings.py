from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import time
from enum import Enum
from pydantic import BaseModel


class DNSStatus(str, Enum):
    ok = "ok"
    nok = "nok"
    unchecked = "unchecked"


class DomainAlias(BaseModel):
    """Email alias configuration for a domain"""
    email: str
    name: str
    username: str  # SMTP username
    password_ref: str  # Reference to encrypted password
    active: bool = True


class DomainConfig(BaseModel):
    """Complete domain configuration with SMTP and aliases"""
    domain: str
    display_name: str
    
    # SMTP Configuration
    smtp_host: str
    smtp_port: int
    use_tls: bool = True
    use_ssl: bool = False
    
    # Email aliases (Christian & Victor per domain)
    aliases: List[DomainAlias]
    
    # Limits & Throttling
    daily_limit: int = 1000
    hourly_limit: int = 100
    throttle_minutes: int = 20
    
    # DNS Status
    spf_status: DNSStatus = DNSStatus.ok
    dkim_status: DNSStatus = DNSStatus.ok
    dmarc_status: DNSStatus = DNSStatus.unchecked
    
    # Reputation
    reputation_score: str = "good"  # good/fair/poor
    active: bool = True


class Settings(SQLModel, table=True):
    __tablename__ = "settings"
    
    id: str = Field(primary_key=True, default="singleton")
    
    # Timezone and sending window
    timezone: str = Field(default="Europe/Amsterdam")
    sending_window_start: str = Field(default="08:00")  # Store as string for simplicity
    sending_window_end: str = Field(default="17:00")
    sending_days: List[str] = Field(default=["Mon", "Tue", "Wed", "Thu", "Fri"], sa_column=Column(JSON))
    
    # Throttling
    throttle_minutes: int = Field(default=20)
    
    # Domains (hard-coded in MVP) - Punthelder domains (simple list for backward compatibility)
    domains: List[str] = Field(
        default=[
            "punthelder-marketing.nl",
            "punthelder-seo.nl", 
            "punthelder-vindbaarheid.nl",
            "punthelder-zoekmachine.nl"
        ],
        sa_column=Column(JSON)
    )
    
    # Extended domain configuration with aliases and SMTP settings
    domains_config: List[DomainConfig] = Field(
        default_factory=list,  # Will be populated in service
        sa_column=Column(JSON)
    )
    
    # Editable fields in MVP
    unsubscribe_text: str = Field(default="Uitschrijven", max_length=50)
    tracking_pixel_enabled: bool = Field(default=True)
    
    # Read-only fields
    provider: str = Field(default="SMTP")
    
    # DNS status (read-only in MVP)
    dns_spf: DNSStatus = Field(default=DNSStatus.ok)
    dns_dkim: DNSStatus = Field(default=DNSStatus.ok)
    dns_dmarc: DNSStatus = Field(default=DNSStatus.unchecked)
    
    def generate_unsubscribe_url(self) -> str:
        """Generate unsubscribe URL with secure token"""
        return "https://app.example.com/unsubscribe?token=secure_token_here"
