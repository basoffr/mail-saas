from __future__ import annotations
from typing import List
from html import escape

from app.services.leads_store import LeadsStore


def render_preview(template_id: str, lead_id: str, store: LeadsStore) -> dict:
    """
    Very lightweight preview stub.
    - Retrieves lead from in-memory store.
    - Produces basic HTML/text output and simple warnings for missing fields.
    - Image CID placeholders are simulated.
    """
    lead = store.get(lead_id)
    if not lead:
        # Mirror API shape in router: returning minimal dict here
        return {"html": "", "text": "", "warnings": ["Lead not found"]}

    warnings: List[str] = []

    company = lead.company or ""
    if not company:
        warnings.append("Missing lead.company")

    # Simulate an image slot requirement for 'hero'
    if not lead.image_key:
        warnings.append("Missing per-lead image for slot 'hero'")
        hero_img_tag = '<img alt="placeholder" src="https://via.placeholder.com/600x200?text=No+Image" />'
    else:
        hero_img_tag = f'<img alt="hero" src="https://example.com/assets/{escape(lead.image_key)}.png" />'

    # Construct simple HTML and text
    html = f"""
    <div>
      <h1>Hello {escape(lead.email)}</h1>
      <p>Company: {escape(company) or 'N/A'}</p>
      <div>{hero_img_tag}</div>
    </div>
    """.strip()

    text = f"Hello {lead.email}\nCompany: {company or 'N/A'}\n"

    return {"html": html, "text": text, "warnings": warnings}
