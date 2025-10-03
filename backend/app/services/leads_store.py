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
    list_name: Optional[str] = None
    last_emailed_at: Optional[datetime] = None
    last_open_at: Optional[datetime] = None
    vars: dict = field(default_factory=dict)
    stopped: bool = False
    deleted_at: Optional[datetime] = None
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
            list_name=self.list_name,
            last_emailed_at=self.last_emailed_at,
            last_open_at=self.last_open_at,
            vars=self.vars,
            stopped=self.stopped,
            deleted_at=self.deleted_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=(self.deleted_at is not None),
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
        list_name: Optional[str] = None,
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
                list_name=list_name,
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
            if list_name:
                rec.list_name = list_name
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
        list_name: Optional[str] = None,
        is_complete: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> Tuple[List[LeadOut], int]:
        # Filter deleted leads UNLESS explicitly requested
        if include_deleted:
            data = list(self._leads)
        else:
            data = [r for r in self._leads if r.deleted_at is None]
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
        if list_name is not None:
            data = [r for r in data if r.list_name == list_name]
        if is_complete is not None:
            # For is_complete filter, we need to import the enrichment service
            from app.services.lead_enrichment import check_lead_is_complete
            from app.models.lead import Lead
            
            # Convert _LeadRec to Lead model for checking
            filtered = []
            for r in data:
                lead = Lead(
                    id=r.id,
                    email=r.email,
                    company=r.company,
                    url=r.url,
                    domain=r.domain,
                    status=r.status,
                    tags=r.tags,
                    image_key=r.image_key,
                    list_name=r.list_name,
                    vars=r.vars,
                    stopped=r.stopped,
                    created_at=r.created_at,
                    updated_at=r.updated_at
                )
                if check_lead_is_complete(lead) == is_complete:
                    filtered.append(r)
            data = filtered
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
    
    def soft_delete(self, lead_id: str) -> bool:
        """Soft delete a lead by setting deleted_at timestamp.
        
        Returns True if successful, False if lead not found.
        """
        for rec in self._leads:
            if rec.id == lead_id:
                rec.deleted_at = _now()
                rec.updated_at = _now()
                return True
        return False
    
    def soft_delete_bulk(self, lead_ids: List[str]) -> Tuple[List[str], List[str]]:
        """Soft delete multiple leads.
        
        Returns (deleted_ids, failed_ids)
        """
        deleted = []
        failed = []
        
        for lead_id in lead_ids:
            if self.soft_delete(lead_id):
                deleted.append(lead_id)
            else:
                failed.append(lead_id)
        
        return deleted, failed
    
    def restore(self, lead_id: str) -> bool:
        """Restore a soft-deleted lead by clearing deleted_at.
        
        Returns True if successful, False if lead not found.
        """
        for rec in self._leads:
            if rec.id == lead_id:
                rec.deleted_at = None
                rec.updated_at = _now()
                return True
        return False
    
    def restore_bulk(self, lead_ids: List[str]) -> Tuple[List[str], List[str]]:
        """Restore multiple soft-deleted leads.
        
        Returns (restored_ids, failed_ids)
        """
        restored = []
        failed = []
        
        for lead_id in lead_ids:
            if self.restore(lead_id):
                restored.append(lead_id)
            else:
                failed.append(lead_id)
        
        return restored, failed
    
    def get_deleted_leads(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None
    ) -> Tuple[List[LeadOut], int]:
        """Get all soft-deleted leads (for trash view).
        
        Returns (leads, total_count)
        """
        data = [r for r in self._leads if r.deleted_at is not None]
        
        if search:
            q = search.lower()
            data = [
                r for r in data
                if q in r.email.lower()
                or (r.company or "").lower().find(q) != -1
            ]
        
        total = len(data)
        start = (page - 1) * page_size
        end = start + page_size
        
        return [r.to_out() for r in data[start:end]], total


# Global instance
leads_store = LeadsStore()
