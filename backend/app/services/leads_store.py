from __future__ import annotations
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from app.schemas.lead import LeadOut, LeadDetail, LeadStatus


def _now() -> datetime:
    return datetime.utcnow()


@dataclass
class _LeadRec:
    id: str
    email: str
    company: Optional[str] = None
    url: Optional[str] = None
    domain: Optional[str] = None
    status: LeadStatus = LeadStatus.active
    tags: List[str] = field(default_factory=list)
    image_key: Optional[str] = None
    last_emailed_at: Optional[datetime] = None
    last_open_at: Optional[datetime] = None
    vars: dict = field(default_factory=dict)
    stopped: bool = False
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_out(self) -> LeadOut:
        return LeadOut(
            id=self.id,
            email=self.email,
            company=self.company,
            url=self.url,
            domain=self.domain,
            status=self.status,
            tags=list(self.tags),
            image_key=self.image_key,
            last_emailed_at=self.last_emailed_at,
            last_open_at=self.last_open_at,
            vars=self.vars,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_detail(self) -> LeadDetail:
        # LeadDetail now inherits vars from LeadOut
        return LeadDetail(**self.to_out().model_dump())


class LeadsStore:
    def __init__(self) -> None:
        self._leads: List[_LeadRec] = []

    def _find_index_by_email(self, email: str) -> Optional[int]:
        for i, rec in enumerate(self._leads):
            if rec.email.lower() == email.lower():
                return i
        return None

    def upsert(
        self,
        *,
        email: str,
        company: Optional[str] = None,
        url: Optional[str] = None,
        domain: Optional[str] = None,
        status: LeadStatus = LeadStatus.active,
        tags: Optional[List[str]] = None,
        image_key: Optional[str] = None,
        vars: Optional[dict] = None,
        last_emailed_at: Optional[datetime] = None,
        last_open_at: Optional[datetime] = None,
    ) -> Tuple[bool, _LeadRec]:
        """Insert or update by email. Returns (created, record). Vars merge on update.
        - Do not overwrite image_key if new value is empty.
        """
        idx = self._find_index_by_email(email)
        if idx is None:
            rec = _LeadRec(
                id=str(uuid4()),
                email=email,
                company=company,
                url=url,
                domain=domain,
                status=status,
                tags=list(tags or []),
                image_key=image_key,
                vars=dict(vars or {}),
                last_emailed_at=last_emailed_at,
                last_open_at=last_open_at,
            )
            self._leads.append(rec)
            return True, rec
        else:
            rec = self._leads[idx]
            # update non-empty basic fields
            if company:
                rec.company = company
            if url:
                rec.url = url
            if domain:
                rec.domain = domain
            if status:
                rec.status = status
            if tags is not None:
                rec.tags = list(tags)
            if image_key:
                rec.image_key = image_key
            if vars:
                rec.vars.update(vars)
            if last_emailed_at:
                rec.last_emailed_at = last_emailed_at
            if last_open_at:
                rec.last_open_at = last_open_at
            rec.updated_at = _now()
            return False, rec

    def get(self, lead_id: str) -> Optional[LeadDetail]:
        for rec in self._leads:
            if rec.id == lead_id:
                return rec.to_detail()
        return None
    
    def get_by_id(self, lead_id: str) -> Optional[LeadDetail]:
        """Alias for get method to match expected interface"""
        return self.get(lead_id)

    def query(
        self,
        *,
        page: int,
        page_size: int,
        status: Optional[List[LeadStatus]] = None,
        domain_tld: Optional[List[str]] = None,
        has_image: Optional[bool] = None,
        has_var: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[LeadOut], int]:
        data = list(self._leads)
        if status:
            sset = set(status)
            data = [r for r in data if r.status in sset]
        if domain_tld:
            tlds = set([t.lower() for t in domain_tld])
            data = [
                r
                for r in data
                if r.domain and any(r.domain.lower().endswith(t) for t in tlds)
            ]
        if has_image is not None:
            data = [r for r in data if (r.image_key is not None) == has_image]
        if has_var is not None:
            data = [r for r in data if (len(r.vars) > 0) == has_var]
        if search:
            q = search.lower()
            data = [
                r
                for r in data
                if q in r.email.lower()
                or (r.company or "").lower().find(q) != -1
                or (r.domain or "").lower().find(q) != -1
            ]
        total = len(data)
        start = (page - 1) * page_size
        end = start + page_size
        return [r.to_out() for r in data[start:end]], total

    def stop_lead(self, lead_id: str) -> int:
        """Stop a lead and cancel all future messages. Returns count of canceled messages."""
        for rec in self._leads:
            if rec.id == lead_id:
                rec.stopped = True
                rec.updated_at = _now()
                # TODO: Cancel queued messages in campaign scheduler
                # For now, return 0 as we don't have message queue implemented yet
                return 0
        return 0

    def is_stopped(self, lead_id: str) -> bool:
        """Check if a lead is stopped."""
        for rec in self._leads:
            if rec.id == lead_id:
                return rec.stopped
        return False
    
    def update_status(self, lead_id: str, status: LeadStatus) -> bool:
        """Update lead status (e.g., for unsubscribe). Returns True if found."""
        for rec in self._leads:
            if rec.id == lead_id:
                rec.status = status
                rec.updated_at = _now()
                return True
        return False


# Global instance
leads_store = LeadsStore()
