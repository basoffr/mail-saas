from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class ImportErrorItem:
    row: int
    field: str
    reason: str


@dataclass
class ImportJobRecord:
    id: str
    filename: str
    status: str  # queued|running|succeeded|failed
    progress: float
    inserted: int
    updated: int
    skipped: int
    errors: List[ImportErrorItem] = field(default_factory=list)
    startedAt: datetime = field(default_factory=datetime.utcnow)
    finishedAt: Optional[datetime] = None


class ImportJobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, ImportJobRecord] = {}

    def create(self, *, job_id: str, filename: str) -> ImportJobRecord:
        rec = ImportJobRecord(
            id=job_id,
            filename=filename,
            status="running",
            progress=0.0,
            inserted=0,
            updated=0,
            skipped=0,
        )
        self._jobs[job_id] = rec
        return rec

    def get(self, job_id: str) -> Optional[ImportJobRecord]:
        return self._jobs.get(job_id)

    def update_progress(
        self,
        job_id: str,
        *,
        progress: float,
        inserted: Optional[int] = None,
        updated: Optional[int] = None,
        skipped: Optional[int] = None,
        status: Optional[str] = None,
        errors: Optional[List[ImportErrorItem]] = None,
    ) -> Optional[ImportJobRecord]:
        rec = self._jobs.get(job_id)
        if not rec:
            return None
        rec.progress = progress
        if inserted is not None:
            rec.inserted = inserted
        if updated is not None:
            rec.updated = updated
        if skipped is not None:
            rec.skipped = skipped
        if errors is not None:
            rec.errors = errors
        if status is not None:
            rec.status = status
            if status in ("succeeded", "failed"):
                rec.finishedAt = datetime.utcnow()
        return rec


# global singleton for MVP
import_job_store = ImportJobStore()
