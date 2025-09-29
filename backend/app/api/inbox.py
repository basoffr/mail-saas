from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from loguru import logger

from ..core.auth import require_auth
from ..schemas.inbox import (
    InboxMessagesResponse, FetchResponse, MarkReadResponseWrapped,
    InboxRunsResponse, InboxQuery
)
from ..schemas.common import DataResponse
from ..services.inbox.accounts import MailAccountService
from ..services.inbox.fetch_runner import FetchRunner, MailMessageStore
from ..services.inbox.linker import MessageLinker

# Initialize services (in production, use dependency injection)
accounts_service = MailAccountService()
messages_store = MailMessageStore()

# Import existing stores for linking (mock references)
class MockLeadsStore:
    def get_all(self):
        return [
            type('Lead', (), {'id': 'lead-001', 'email': 'john.doe@gmail.com'}),
            type('Lead', (), {'id': 'lead-002', 'email': 'sarah.smith@outlook.com'}),
        ]

class MockMessagesStore:
    def get_all(self):
        return [
            type('Message', (), {
                'id': 'msg-out-001', 
                'campaign_id': 'campaign-001', 
                'lead_id': 'lead-001',
                'smtp_message_id': 'campaign-msg-001@domain1.com',
                'sent_at': None
            })
        ]

class MockCampaignsStore:
    def get_all(self):
        return []

# Initialize linker with mock stores
message_linker = MessageLinker(
    messages_store=MockMessagesStore(),
    leads_store=MockLeadsStore(),
    campaigns_store=MockCampaignsStore()
)

# Initialize fetch runner
fetch_runner = FetchRunner(
    accounts_service=accounts_service,
    messages_store=messages_store,
    message_linker=message_linker
)

router = APIRouter(prefix="/inbox", tags=["inbox"])




@router.post("/fetch", response_model=FetchResponse)
async def start_fetch(user: Dict[str, Any] = Depends(require_auth)):
    """
    Start async fetch job for all active IMAP accounts.
    Respects minimum interval guard (2 minutes).
    """
    try:
        logger.info(f"Inbox fetch started by user: {user.get('id', 'unknown')}")
        
        run_id = await fetch_runner.start_fetch_all_accounts()
        
        return DataResponse(
            data={'ok': True, 'run_id': run_id},
            error=None
        )
        
    except Exception as e:
        logger.error(f"Fetch start failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start fetch")


@router.get("/messages", response_model=InboxMessagesResponse)
async def list_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    account_id: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None),
    unread: Optional[bool] = Query(None),
    q: Optional[str] = Query(None, description="Search query"),
    from_date: Optional[str] = Query(None, description="ISO date"),
    to_date: Optional[str] = Query(None, description="ISO date"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get inbox messages with filtering and pagination.
    Default sort: received_at desc.
    """
    try:
        query = {
            'page': page,
            'page_size': page_size,
            'account_id': account_id,
            'campaign_id': campaign_id,
            'unread': unread,
            'q': q,
            'from_date': from_date,
            'to_date': to_date
        }
        
        # Get filtered messages
        messages = messages_store.get_by_query(query)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_messages = messages[start_idx:end_idx]
        
        # Add account labels
        accounts = {acc['id']: acc for acc in accounts_service.get_all_accounts()}
        
        for msg in paginated_messages:
            account = accounts.get(msg['account_id'])
            msg['account_label'] = account['label'] if account else 'Unknown Account'
            
            # Add linked entity names (mock implementation)
            if msg.get('linked_campaign_id'):
                msg['linked_campaign_name'] = f"Campaign {msg['linked_campaign_id'][-3:]}"
            if msg.get('linked_lead_id'):
                msg['linked_lead_email'] = msg['from_email']  # Use from_email as lead email
        
        response_data = {
            'items': paginated_messages,
            'total': len(messages)
        }
        
        return DataResponse(data=response_data, error=None)
        
    except Exception as e:
        logger.error(f"Failed to list messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@router.post("/messages/{message_id}/mark-read", response_model=MarkReadResponseWrapped)
async def mark_message_read(
    message_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """
    Mark message as read (app-local, idempotent).
    """
    try:
        success = messages_store.mark_as_read(message_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        logger.info(f"Message marked as read: {message_id}")
        
        return DataResponse(
            data={'ok': True},
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark message as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark message as read")


@router.get("/runs", response_model=InboxRunsResponse)
async def list_fetch_runs(
    account_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get fetch run history (optional endpoint).
    """
    try:
        runs = messages_store.get_runs(account_id)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_runs = runs[start_idx:end_idx]
        
        return DataResponse(data=paginated_runs, error=None)
        
    except Exception as e:
        logger.error(f"Failed to list runs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve runs")
