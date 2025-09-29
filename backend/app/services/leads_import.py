from __future__ import annotations
from typing import Tuple, Set
from pydantic import BaseModel
from fastapi import UploadFile, HTTPException, status
import pandas as pd
import io
import re
from urllib.parse import urlparse
from datetime import datetime

from app.schemas.lead import LeadStatus
from app.services.leads_store import LeadsStore
from app.services.import_jobs import import_job_store, ImportErrorItem

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ImportResult(BaseModel):
    inserted: int
    updated: int
    skipped: int
    jobId: str


def _normalize_key(key: str) -> str:
    key = key.strip().lower()
    key = key.replace(" ", "_").replace("-", "_").replace(".", "_")
    return key


def _domain_from_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        host = urlparse(url).netloc or urlparse("https://" + url).netloc
        if host.startswith("www."):
            host = host[4:]
        return host or None
    except Exception:
        return None


def _extract_root_domain(domain: str | None) -> str | None:
    """Extract root domain for image_key generation"""
    if not domain:
        return None
    try:
        # Remove www prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Extract root (first part before TLD)
        parts = domain.split(".")
        if len(parts) >= 2:
            root = parts[0]
            # Normalize: lowercase, replace underscores with hyphens
            root = root.lower().replace("_", "-")
            # Collapse multiple hyphens
            root = re.sub(r"-+", "-", root)
            return root
        return domain.lower()
    except Exception:
        return None


async def process_import_file(file: UploadFile, store: LeadsStore) -> ImportResult:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

    filename = file.filename
    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv or .xlsx supported")

    content = await file.read()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to parse file")

    if df.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    df.columns = [_normalize_key(c) for c in df.columns]

    if "email" not in df.columns:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Column 'email' is required")

    inserted = 0
    updated = 0
    skipped = 0
    errors: list[ImportErrorItem] = []

    seen: Set[str] = set()

    for _, row in df.iterrows():
        email = str(row.get("email", "")).strip()
        if not email or not EMAIL_RE.match(email):
            skipped += 1
            errors.append(ImportErrorItem(row=int(_)+1, field="email", reason="invalid email"))
            continue
        low_email = email.lower()
        if low_email in seen:
            skipped += 1
            continue
        seen.add(low_email)

        company = row.get("company") or row.get("company_name") or None
        url = row.get("url") or row.get("website") or None
        url = str(url).strip() if isinstance(url, str) else url
        domain = _domain_from_url(url)
        
        # Auto-generate image_key based on root domain
        image_key = None
        if domain:
            root_domain = _extract_root_domain(domain)
            if root_domain:
                image_key = f"{root_domain}_picture"

        # Collect extra vars (exclude known columns)
        known = {"email", "company", "company_name", "url", "website", "image_key"}
        extra_vars = {}
        for c in df.columns:
            if c not in known:
                val = row.get(c)
                if pd.notna(val):
                    extra_vars[c] = val

        created, _rec = store.upsert(
            email=email,
            company=company if company else None,
            url=url,
            domain=domain,
            status=LeadStatus.active,
            image_key=image_key,
            vars=extra_vars if extra_vars else None,
        )
        if created:
            inserted += 1
        else:
            updated += 1

    job_id = f"import-{int(datetime.utcnow().timestamp())}"

    # Create job record and mark as succeeded for MVP (no async worker yet)
    job = import_job_store.create(job_id=job_id, filename=filename)
    import_job_store.update_progress(
        job_id,
        progress=100.0,
        inserted=inserted,
        updated=updated,
        skipped=skipped,
        status="succeeded",
        errors=errors,
    )

    return ImportResult(inserted=inserted, updated=updated, skipped=skipped, jobId=job_id)
