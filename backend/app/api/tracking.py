from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from loguru import logger

from app.services.campaign_store import campaign_store
from app.services.message_sender import MessageSender

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
