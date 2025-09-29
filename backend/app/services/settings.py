from typing import Optional
from app.models.settings import Settings, DNSStatus, DomainConfig, DomainAlias
from app.schemas.settings import SettingsOut, SettingsUpdate, SendingWindow, ThrottleInfo, EmailInfra, DomainConfigOut, DomainAliasOut
import secrets


class SettingsService:
    def __init__(self):
        # In-memory singleton for MVP
        self._settings: Optional[Settings] = None
        self._initialize_default_settings()
    
    def _create_punthelder_domains_config(self) -> list[DomainConfig]:
        """Create domain configuration based on Excel data"""
        return [
            DomainConfig(
                domain="punthelder-marketing.nl",
                display_name="Punthelder Marketing",
                smtp_host="mail.punthelder-marketing.nl",
                smtp_port=587,
                use_tls=True,
                aliases=[
                    DomainAlias(
                        email="christian@punthelder-marketing.nl",
                        name="Christian Punthelder",
                        username="christian@punthelder-marketing.nl",
                        password_ref="vault://smtp/punthelder-marketing/christian",
                        active=True
                    ),
                    DomainAlias(
                        email="victor@punthelder-marketing.nl",
                        name="Victor Punthelder",
                        username="victor@punthelder-marketing.nl",
                        password_ref="vault://smtp/punthelder-marketing/victor",
                        active=True
                    )
                ],
                daily_limit=1000,
                throttle_minutes=20,
                spf_status=DNSStatus.ok,
                dkim_status=DNSStatus.ok,
                dmarc_status=DNSStatus.unchecked
            ),
            DomainConfig(
                domain="punthelder-seo.nl",
                display_name="Punthelder SEO",
                smtp_host="mail.punthelder-seo.nl",
                smtp_port=587,
                use_tls=True,
                aliases=[
                    DomainAlias(
                        email="christian@punthelder-seo.nl",
                        name="Christian Punthelder",
                        username="christian@punthelder-seo.nl",
                        password_ref="vault://smtp/punthelder-seo/christian",
                        active=True
                    ),
                    DomainAlias(
                        email="victor@punthelder-seo.nl",
                        name="Victor Punthelder",
                        username="victor@punthelder-seo.nl",
                        password_ref="vault://smtp/punthelder-seo/victor",
                        active=True
                    )
                ],
                daily_limit=1000,
                throttle_minutes=20,
                spf_status=DNSStatus.ok,
                dkim_status=DNSStatus.ok,
                dmarc_status=DNSStatus.unchecked
            ),
            DomainConfig(
                domain="punthelder-vindbaarheid.nl",
                display_name="Punthelder Vindbaarheid",
                smtp_host="mail.punthelder-vindbaarheid.nl",
                smtp_port=587,
                use_tls=True,
                aliases=[
                    DomainAlias(
                        email="christian@punthelder-vindbaarheid.nl",
                        name="Christian Punthelder",
                        username="christian@punthelder-vindbaarheid.nl",
                        password_ref="vault://smtp/punthelder-vindbaarheid/christian",
                        active=True
                    ),
                    DomainAlias(
                        email="victor@punthelder-vindbaarheid.nl",
                        name="Victor Punthelder",
                        username="victor@punthelder-vindbaarheid.nl",
                        password_ref="vault://smtp/punthelder-vindbaarheid/victor",
                        active=True
                    )
                ],
                daily_limit=1000,
                throttle_minutes=20,
                spf_status=DNSStatus.ok,
                dkim_status=DNSStatus.ok,
                dmarc_status=DNSStatus.unchecked
            ),
            DomainConfig(
                domain="punthelder-zoekmachine.nl",
                display_name="Punthelder Zoekmachine",
                smtp_host="mail.punthelder-zoekmachine.nl",
                smtp_port=587,
                use_tls=True,
                aliases=[
                    DomainAlias(
                        email="christian@punthelder-zoekmachine.nl",
                        name="Christian Punthelder",
                        username="christian@punthelder-zoekmachine.nl",
                        password_ref="vault://smtp/punthelder-zoekmachine/christian",
                        active=True
                    ),
                    DomainAlias(
                        email="victor@punthelder-zoekmachine.nl",
                        name="Victor Punthelder",
                        username="victor@punthelder-zoekmachine.nl",
                        password_ref="vault://smtp/punthelder-zoekmachine/victor",
                        active=True
                    )
                ],
                daily_limit=1000,
                throttle_minutes=20,
                spf_status=DNSStatus.ok,
                dkim_status=DNSStatus.ok,
                dmarc_status=DNSStatus.unchecked
            )
        ]
    
    def _initialize_default_settings(self):
        """Initialize default settings if not exists"""
        if self._settings is None:
            self._settings = Settings(
                id="singleton",
                timezone="Europe/Amsterdam",
                sending_window_start="08:00",
                sending_window_end="17:00",
                sending_days=["Mon", "Tue", "Wed", "Thu", "Fri"],
                throttle_minutes=20,
                domains=[
                    "punthelder-marketing.nl",
                    "punthelder-seo.nl", 
                    "punthelder-vindbaarheid.nl",
                    "punthelder-zoekmachine.nl"
                ],
                domains_config=self._create_punthelder_domains_config(),
                unsubscribe_text="Uitschrijven",
                tracking_pixel_enabled=True,
                provider="SMTP",
                dns_spf=DNSStatus.ok,
                dns_dkim=DNSStatus.ok,
                dns_dmarc=DNSStatus.unchecked
            )
    
    def get_settings(self) -> SettingsOut:
        """Get current settings"""
        if self._settings is None:
            self._initialize_default_settings()
        
        # Convert to frontend format
        return SettingsOut(
            timezone=self._settings.timezone,
            window=SendingWindow(
                days=self._settings.sending_days,
                from_time=self._settings.sending_window_start,
                to=self._settings.sending_window_end
            ),
            throttle=ThrottleInfo(
                emails_per=1,
                minutes=self._settings.throttle_minutes
            ),
            domains=self._settings.domains,
            domains_config=self._convert_domains_config_to_frontend(),
            unsubscribe_text=self._settings.unsubscribe_text,
            unsubscribe_url=self._generate_unsubscribe_url(),
            tracking_pixel_enabled=self._settings.tracking_pixel_enabled,
            email_infra=EmailInfra(
                current=self._settings.provider,
                provider=None,
                provider_enabled=False,
                dns={
                    "spf": self._settings.dns_spf == DNSStatus.ok,
                    "dkim": self._settings.dns_dkim == DNSStatus.ok,
                    "dmarc": self._settings.dns_dmarc == DNSStatus.ok
                }
            )
        )
    
    def update_settings(self, updates: SettingsUpdate) -> SettingsOut:
        """Update settings (only editable fields in MVP)"""
        if self._settings is None:
            self._initialize_default_settings()
        
        # Only allow updates to specific fields in MVP
        if updates.unsubscribe_text is not None:
            self._settings.unsubscribe_text = updates.unsubscribe_text
        
        if updates.tracking_pixel_enabled is not None:
            self._settings.tracking_pixel_enabled = updates.tracking_pixel_enabled
        
        return self.get_settings()
    
    def _generate_unsubscribe_url(self) -> str:
        """Generate secure unsubscribe URL"""
        token = secrets.token_urlsafe(32)
        return f"https://app.example.com/unsubscribe?token={token}"
    
    def _convert_domains_config_to_frontend(self) -> list[DomainConfigOut]:
        """Convert domain config to frontend format"""
        if not self._settings or not self._settings.domains_config:
            return []
        
        result = []
        for domain_config in self._settings.domains_config:
            # Convert aliases (hide sensitive info)
            aliases_out = [
                DomainAliasOut(
                    email=alias.email,
                    name=alias.name,
                    active=alias.active
                )
                for alias in domain_config.aliases
            ]
            
            # Convert domain config
            domain_out = DomainConfigOut(
                domain=domain_config.domain,
                display_name=domain_config.display_name,
                smtp_host=domain_config.smtp_host,
                smtp_port=domain_config.smtp_port,
                use_tls=domain_config.use_tls,
                aliases=aliases_out,
                daily_limit=domain_config.daily_limit,
                throttle_minutes=domain_config.throttle_minutes,
                dns_status={
                    "spf": domain_config.spf_status.value,
                    "dkim": domain_config.dkim_status.value,
                    "dmarc": domain_config.dmarc_status.value
                },
                reputation_score=domain_config.reputation_score,
                active=domain_config.active
            )
            result.append(domain_out)
        
        return result
    
    def validate_unsubscribe_text(self, text: str) -> bool:
        """Validate unsubscribe text length"""
        return 1 <= len(text.strip()) <= 50


# Global service instance
settings_service = SettingsService()
