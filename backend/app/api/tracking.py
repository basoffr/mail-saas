from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response, HTMLResponse
from loguru import logger
from datetime import datetime

from app.services.campaign_store import campaign_store
from app.services.message_sender import MessageSender
from app.services.leads_store import leads_store
from app.models.lead import LeadStatus

router = APIRouter(prefix="/track", tags=["tracking"])

# Initialize services
sender = MessageSender()

# 1x1 transparent GIF pixel (base64 encoded)
PIXEL_GIF = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3b'


@router.get("/open.gif")
async def track_open(
    request: Request,
    m: str = Query(..., description="Message ID"),
    t: str = Query(..., description="Security token")
):
    """
    Track email open events via 1x1 pixel GIF.
    Returns transparent pixel and logs open event.
    """
    
    try:
        # Get message
        message = campaign_store.get_message(m)
        if not message:
            logger.warning(f"Open tracking: message {m} not found")
            return _return_pixel()
        
        # Validate token (simplified for MVP)
        expected_token = sender._generate_token(m)
        if t != expected_token:
            logger.warning(f"Open tracking: invalid token for message {m}")
            return _return_pixel()
        
        # Extract client info
        user_agent = request.headers.get("user-agent")
        client_ip = request.client.host if request.client else None
        
        # Log open event
        await sender.handle_open(message, user_agent, client_ip)
        
        logger.info(f"Tracked open for message {m} from {client_ip}")
        
    except Exception as e:
        logger.error(f"Error tracking open for message {m}: {str(e)}")
        # Always return pixel even on error to avoid broken images
    
    return _return_pixel()


def _return_pixel() -> Response:
    """Return 1x1 transparent GIF pixel."""
    return Response(
        content=PIXEL_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@router.post("/unsubscribe")
async def unsubscribe(
    request: Request,
    m: str = Query(..., description="Message ID"),
    t: str = Query(..., description="Security token")
):
    """
    Handle unsubscribe requests.
    Validates token and marks lead as suppressed.
    
    Args:
        m: Message ID
        t: Security token (same as tracking pixel)
    
    Returns:
        HTML confirmation page
    """
    
    try:
        # Get message
        message = campaign_store.get_message(m)
        if not message:
            logger.warning(f"Unsubscribe: message {m} not found")
            return _unsubscribe_error_page("Invalid unsubscribe link")
        
        # Validate token
        expected_token = sender._generate_token(m)
        if t != expected_token:
            logger.warning(f"Unsubscribe: invalid token for message {m}")
            return _unsubscribe_error_page("Invalid or expired link")
        
        # Get lead
        lead = leads_store.get(message.lead_id)
        if not lead:
            logger.warning(f"Unsubscribe: lead {message.lead_id} not found")
            return _unsubscribe_error_page("Lead not found")
        
        # Check if already unsubscribed
        if lead.status == LeadStatus.suppressed:
            logger.info(f"Lead {lead.id} ({lead.email}) already unsubscribed")
            return _unsubscribe_success_page(lead.email, already_unsubscribed=True)
        
        # Mark lead as suppressed
        leads_store.update_status(message.lead_id, LeadStatus.suppressed)
        
        # Log unsubscribe event
        from app.models.campaign import MessageEvent, MessageEventType
        import uuid
        
        event = MessageEvent(
            id=str(uuid.uuid4()),
            message_id=message.id,
            event_type=MessageEventType.failed,  # Using failed as proxy for unsubscribe
            meta={"reason": "unsubscribed", "timestamp": datetime.utcnow().isoformat()},
            created_at=datetime.utcnow()
        )
        campaign_store.events[event.id] = event
        
        logger.info(f"Lead {lead.id} ({lead.email}) unsubscribed via message {m}")
        
        return _unsubscribe_success_page(lead.email, already_unsubscribed=False)
        
    except Exception as e:
        logger.error(f"Error processing unsubscribe for message {m}: {str(e)}")
        return _unsubscribe_error_page("An error occurred. Please try again.")


def _unsubscribe_success_page(email: str, already_unsubscribed: bool = False) -> HTMLResponse:
    """Return unsubscribe success HTML page."""
    
    if already_unsubscribed:
        message = f"You have already unsubscribed."
        subtitle = "No further action is needed."
    else:
        message = "You have been successfully unsubscribed."
        subtitle = "You will no longer receive emails from us."
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Unsubscribed</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 48px;
                max-width: 500px;
                text-align: center;
            }}
            .icon {{
                width: 64px;
                height: 64px;
                background: #10b981;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 24px;
            }}
            .icon svg {{
                width: 32px;
                height: 32px;
                stroke: white;
            }}
            h1 {{
                color: #1f2937;
                font-size: 24px;
                margin: 0 0 12px;
                font-weight: 600;
            }}
            p {{
                color: #6b7280;
                font-size: 16px;
                line-height: 1.6;
                margin: 0 0 8px;
            }}
            .email {{
                color: #374151;
                font-weight: 500;
            }}
            .footer {{
                margin-top: 32px;
                padding-top: 24px;
                border-top: 1px solid #e5e7eb;
                color: #9ca3af;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            <h1>{message}</h1>
            <p>{subtitle}</p>
            <p class="email">{email}</p>
            <div class="footer">
                If this was a mistake, please contact us.
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)


def _unsubscribe_error_page(error_message: str) -> HTMLResponse:
    """Return unsubscribe error HTML page."""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 48px;
                max-width: 500px;
                text-align: center;
            }}
            .icon {{
                width: 64px;
                height: 64px;
                background: #ef4444;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 24px;
            }}
            .icon svg {{
                width: 32px;
                height: 32px;
                stroke: white;
            }}
            h1 {{
                color: #1f2937;
                font-size: 24px;
                margin: 0 0 12px;
                font-weight: 600;
            }}
            p {{
                color: #6b7280;
                font-size: 16px;
                line-height: 1.6;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </div>
            <h1>Error</h1>
            <p>{error_message}</p>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=400)
