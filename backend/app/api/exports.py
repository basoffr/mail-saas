from fastapi import APIRouter, Depends, Response
from typing import List
import csv
import io
from datetime import datetime

from app.core.auth import require_auth
from app.services.campaign_store import campaign_store

router = APIRouter(dependencies=[Depends(require_auth)])


@router.get("/exports/sends.csv")
async def export_sends_csv():
    """
    Export sends log as CSV with exact column order from implementation plan:
    1) campaign_id, 2) lead_id, 3) domain, 4) alias, 5) step_no, 6) template_id,
    7) scheduled_at, 8) sent_at, 9) status, 10) with_image, 11) with_report,
    12) error_code, 13) error_message
    """
    
    # Get all messages from campaign store
    messages = campaign_store.get_all_messages()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header (exact order from plan)
    writer.writerow([
        "campaign_id",
        "lead_id", 
        "domain",
        "alias",
        "step_no",
        "template_id",
        "scheduled_at",
        "sent_at",
        "status",
        "with_image",
        "with_report",
        "error_code",
        "error_message"
    ])
    
    # Write data rows
    for message in messages:
        # Get campaign to get template_id
        campaign = campaign_store.get_campaign(message.campaign_id)
        template_id = campaign.template_id if campaign else ""
        
        # Parse error for code/message
        error_code = ""
        error_message = ""
        if message.last_error:
            # Simple error parsing - could be enhanced
            error_message = message.last_error
            if message.status == "failed":
                error_code = "SEND_FAILED"
            elif message.status == "bounced":
                error_code = "BOUNCED"
        
        writer.writerow([
            message.campaign_id,
            message.lead_id,
            message.domain_used,
            message.alias,
            message.mail_number,  # step_no
            template_id,
            message.scheduled_at.isoformat() if message.scheduled_at else "",
            message.sent_at.isoformat() if message.sent_at else "",
            message.status,
            message.with_image,
            message.with_report,
            error_code,
            error_message
        ])
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sends_log_{timestamp}.csv"
    
    # Return CSV response
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
