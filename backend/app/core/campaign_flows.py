from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta


@dataclass(frozen=True)
class FlowStep:
    """A single step in a campaign flow."""
    mail_number: int
    alias: str  # "christian" or "victor"
    workdays_offset: int  # Days from campaign start


@dataclass(frozen=True)
class CampaignFlow:
    """Hard-coded campaign flow per domain."""
    version: int
    domain: str
    steps: List[FlowStep]
    
    def get_step_by_mail_number(self, mail_number: int) -> Optional[FlowStep]:
        """Get flow step by mail number."""
        for step in self.steps:
            if step.mail_number == mail_number:
                return step
        return None
    
    def get_alias_for_mail(self, mail_number: int) -> str:
        """Get alias for specific mail number."""
        step = self.get_step_by_mail_number(mail_number)
        return step.alias if step else "christian"  # Default fallback


# Hard-coded domain flows (v1-v4)
# v1 = vindbaarheid, v2 = marketing, v3 = seo, v4 = zoekmachine
DOMAIN_FLOWS = {
    "punthelder-vindbaarheid.nl": CampaignFlow(
        version=1,
        domain="punthelder-vindbaarheid.nl",
        steps=[
            FlowStep(mail_number=1, alias="christian", workdays_offset=0),
            FlowStep(mail_number=2, alias="christian", workdays_offset=3),
            FlowStep(mail_number=3, alias="victor", workdays_offset=6),
            FlowStep(mail_number=4, alias="victor", workdays_offset=9),
        ]
    ),
    "punthelder-marketing.nl": CampaignFlow(
        version=2,
        domain="punthelder-marketing.nl",
        steps=[
            FlowStep(mail_number=1, alias="christian", workdays_offset=0),
            FlowStep(mail_number=2, alias="christian", workdays_offset=3),
            FlowStep(mail_number=3, alias="victor", workdays_offset=6),
            FlowStep(mail_number=4, alias="victor", workdays_offset=9),
        ]
    ),
    "punthelder-seo.nl": CampaignFlow(
        version=3,
        domain="punthelder-seo.nl",
        steps=[
            FlowStep(mail_number=1, alias="christian", workdays_offset=0),
            FlowStep(mail_number=2, alias="christian", workdays_offset=3),
            FlowStep(mail_number=3, alias="victor", workdays_offset=6),
            FlowStep(mail_number=4, alias="victor", workdays_offset=9),
        ]
    ),
    "punthelder-zoekmachine.nl": CampaignFlow(
        version=4,
        domain="punthelder-zoekmachine.nl",
        steps=[
            FlowStep(mail_number=1, alias="christian", workdays_offset=0),
            FlowStep(mail_number=2, alias="christian", workdays_offset=3),
            FlowStep(mail_number=3, alias="victor", workdays_offset=6),
            FlowStep(mail_number=4, alias="victor", workdays_offset=9),
        ]
    )
}


def get_flow_for_domain(domain: str) -> Optional[CampaignFlow]:
    """Get campaign flow for domain."""
    return DOMAIN_FLOWS.get(domain)


def get_all_flows() -> Dict[str, CampaignFlow]:
    """Get all available flows."""
    return DOMAIN_FLOWS.copy()


def calculate_mail_schedule(campaign_start: datetime, flow: CampaignFlow) -> Dict[int, datetime]:
    """Calculate scheduled dates for all mails in flow."""
    from app.core.sending_policy import SENDING_POLICY
    
    schedule = {}
    
    for step in flow.steps:
        # Calculate target date (workdays from start)
        target_date = campaign_start
        workdays_added = 0
        
        while workdays_added < step.workdays_offset:
            target_date += timedelta(days=1)
            if SENDING_POLICY.is_valid_sending_day(target_date):
                workdays_added += 1
        
        # Get next valid slot for this date
        scheduled_at = SENDING_POLICY.get_next_valid_slot(target_date)
        schedule[step.mail_number] = scheduled_at
    
    return schedule


def get_alias_mapping(domain: str) -> Dict[str, Dict[str, str]]:
    """Get alias configuration for From/Reply-To headers (domain-specific).
    
    Args:
        domain: Campaign domain (e.g., "punthelder-vindbaarheid.nl")
    
    Returns:
        Alias config with domain-specific email addresses
    """
    return {
        "christian": {
            "name": "Christian",
            "email": f"christian@{domain}",
            "role": "initial_contact"
        },
        "victor": {
            "name": "Victor", 
            "email": f"victor@{domain}",
            "role": "follow_up"
        }
    }


def get_followup_headers(mail_number: int, domain: str) -> Dict[str, str]:
    """Get From/Reply-To headers for follow-up mails (domain-specific).
    
    Args:
        mail_number: Mail number (1-4)
        domain: Campaign domain
    
    Returns:
        From/Reply-To headers with domain-specific addresses
    """
    if mail_number in [3, 4]:  # Victor mails
        return {
            "from": f"victor@{domain}",
            "reply_to": f"christian@{domain}"
        }
    else:  # Christian mails
        return {
            "from": f"christian@{domain}", 
            "reply_to": f"christian@{domain}"
        }


def validate_domain(domain: str) -> bool:
    """Validate if domain has a configured flow."""
    return domain in DOMAIN_FLOWS


def get_flow_summary() -> List[Dict]:
    """Get summary of all flows for UI display."""
    summaries = []
    
    for domain, flow in DOMAIN_FLOWS.items():
        summaries.append({
            "domain": domain,
            "version": flow.version,
            "total_mails": len(flow.steps),
            "aliases": list(set(step.alias for step in flow.steps)),
            "duration_workdays": max(step.workdays_offset for step in flow.steps),
            "steps": [
                {
                    "mail": step.mail_number,
                    "alias": step.alias,
                    "day": step.workdays_offset
                }
                for step in flow.steps
            ]
        })
    
    return summaries
