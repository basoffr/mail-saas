import uuid
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger

from app.core.auth import require_auth
from app.schemas.common import DataResponse
from app.schemas.campaign import (
    CampaignOut, CampaignDetail, CampaignCreatePayload, CampaignsResponse,
    MessageOut, MessagesResponse, CampaignActionResponse, DryRunResponse,
    ResendPayload, CampaignQuery, MessageQuery
)
from app.models.campaign import Campaign, CampaignAudience, CampaignStatus, MessageStatus
from app.services.campaign_store import campaign_store
from app.services.campaign_scheduler import CampaignScheduler
from app.services.message_sender import MessageSender
from app.services.leads_store import leads_store

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# Initialize services
scheduler = CampaignScheduler()
sender = MessageSender()


@router.get("", response_model=DataResponse[CampaignsResponse])
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: List[CampaignStatus] = Query(None),
    search: str = Query(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """List campaigns with filtering and pagination."""
    try:
        query = CampaignQuery(
            page=page,
            page_size=page_size,
            status=status,
            search=search
        )
        
        campaigns, total = campaign_store.list_campaigns(query)
        
        response = CampaignsResponse(
            items=[CampaignOut.model_validate(c.__dict__) for c in campaigns],
            total=total
        )
        
        logger.info(f"Listed {len(campaigns)} campaigns (total: {total})")
        return DataResponse(data=response)
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=DataResponse[Dict[str, str]])
async def create_campaign(
    payload: CampaignCreatePayload,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create a new campaign."""
    try:
        # Create campaign
        campaign = Campaign(
            id=str(uuid.uuid4()),
            name=payload.name,
            template_id=payload.template_id,
            start_at=payload.schedule.start_at if payload.schedule.start_mode == "scheduled" else None,
            status=CampaignStatus.draft,
            followup_enabled=payload.followup.enabled,
            followup_days=payload.followup.days,
            followup_attach_report=payload.followup.attach_report
        )
        
        campaign = campaign_store.create_campaign(campaign)
        
        # Create audience snapshot
        audience = CampaignAudience(
            id=str(uuid.uuid4()),
            campaign_id=campaign.id,
            lead_ids=payload.audience.lead_ids or [],
            exclude_suppressed=payload.audience.exclude_suppressed,
            exclude_recent_days=payload.audience.exclude_recent_days,
            one_per_domain=payload.audience.one_per_domain
        )
        
        campaign_store.create_audience(audience)
        
        # If starting now, create and schedule messages
        if payload.schedule.start_mode == "now":
            await _start_campaign(campaign, audience, payload.domains)
        
        logger.info(f"Created campaign {campaign.id}: {campaign.name}")
        return DataResponse(data={"id": campaign.id})
        
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{campaign_id}", response_model=DataResponse[CampaignDetail])
async def get_campaign_detail(
    campaign_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get campaign detail with KPIs and timeline."""
    try:
        campaign = campaign_store.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get KPIs and timeline
        kpis = campaign_store.get_campaign_kpis(campaign_id)
        timeline = campaign_store.get_campaign_timeline(campaign_id)
        
        # Get audience info
        audience = campaign_store.get_audience(campaign_id)
        audience_count = len(audience.lead_ids) if audience else 0
        
        # Get domains used
        messages, _ = campaign_store.list_messages(MessageQuery(campaign_id=campaign_id, page_size=1000))
        domains_used = list(set(m.domain_used for m in messages))
        
        detail = CampaignDetail(
            **campaign.__dict__,
            kpis=kpis,
            timeline=timeline,
            domains_used=domains_used,
            audience_count=audience_count
        )
        
        return DataResponse(data=detail)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign detail: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{campaign_id}/pause", response_model=DataResponse[CampaignActionResponse])
async def pause_campaign(
    campaign_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Pause a running campaign."""
    try:
        campaign = campaign_store.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.status != CampaignStatus.running:
            raise HTTPException(status_code=400, detail="Can only pause running campaigns")
        
        # Update status
        campaign_store.update_campaign_status(campaign_id, CampaignStatus.paused)
        scheduler.pause_campaign(campaign_id)
        
        logger.info(f"Paused campaign {campaign_id}")
        return DataResponse(data=CampaignActionResponse(ok=True, message="Campaign paused"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{campaign_id}/resume", response_model=DataResponse[CampaignActionResponse])
async def resume_campaign(
    campaign_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Resume a paused campaign."""
    try:
        campaign = campaign_store.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.status != CampaignStatus.paused:
            raise HTTPException(status_code=400, detail="Can only resume paused campaigns")
        
        # Update status
        campaign_store.update_campaign_status(campaign_id, CampaignStatus.running)
        scheduler.resume_campaign(campaign_id)
        
        logger.info(f"Resumed campaign {campaign_id}")
        return DataResponse(data=CampaignActionResponse(ok=True, message="Campaign resumed"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{campaign_id}/stop", response_model=DataResponse[CampaignActionResponse])
async def stop_campaign(
    campaign_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Stop a campaign (irreversible)."""
    try:
        campaign = campaign_store.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.status in [CampaignStatus.completed, CampaignStatus.stopped]:
            raise HTTPException(status_code=400, detail="Campaign already stopped")
        
        # Update status
        campaign_store.update_campaign_status(campaign_id, CampaignStatus.stopped)
        scheduler.stop_campaign(campaign_id)
        
        logger.info(f"Stopped campaign {campaign_id}")
        return DataResponse(data=CampaignActionResponse(ok=True, message="Campaign stopped"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{campaign_id}/dry-run", response_model=DataResponse[DryRunResponse])
async def dry_run_campaign(
    campaign_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Simulate campaign planning."""
    try:
        campaign = campaign_store.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get audience
        audience = campaign_store.get_audience(campaign_id)
        if not audience:
            raise HTTPException(status_code=400, detail="Campaign has no audience")
        
        # Simulate planning
        domains = ["domain1.com", "domain2.com", "domain3.com", "domain4.com"]  # Default domains
        lead_count = len(audience.lead_ids)
        
        by_day = scheduler.dry_run_planning(lead_count, domains, campaign.start_at)
        
        response = DryRunResponse(
            by_day=by_day,
            total_planned=lead_count,
            estimated_completion=None  # Could calculate based on throttle
        )
        
        return DataResponse(data=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dry run: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/messages", response_model=DataResponse[MessagesResponse])
async def list_messages(
    campaign_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: List[MessageStatus] = Query(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """List messages for a campaign."""
    try:
        query = MessageQuery(
            page=page,
            page_size=page_size,
            campaign_id=campaign_id,
            status=status
        )
        
        messages, total = campaign_store.list_messages(query)
        
        response = MessagesResponse(
            items=[MessageOut.model_validate(m.__dict__) for m in messages],
            total=total
        )
        
        return DataResponse(data=response)
        
    except Exception as e:
        logger.error(f"Error listing messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/messages/{message_id}/resend", response_model=DataResponse[CampaignActionResponse])
async def resend_message(
    message_id: str,
    payload: ResendPayload,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Resend a failed message."""
    try:
        message = campaign_store.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if message.status != MessageStatus.failed:
            raise HTTPException(status_code=400, detail="Can only resend failed messages")
        
        # Get lead for sending
        lead = leads_store.get_by_id(message.lead_id)
        if not lead:
            raise HTTPException(status_code=400, detail="Lead not found")
        
        # Attempt resend
        success = await sender.retry_failed_message(message, lead, "template_content")
        
        if success:
            logger.info(f"Resent message {message_id}")
            return DataResponse(data=CampaignActionResponse(ok=True, message="Message resent"))
        else:
            return DataResponse(data=CampaignActionResponse(ok=False, message="Resend failed"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _start_campaign(campaign: Campaign, audience: CampaignAudience, domains: List[str]):
    """Start campaign by creating and scheduling messages."""
    
    # Create messages
    messages = scheduler.create_campaign_messages(
        campaign=campaign,
        lead_ids=audience.lead_ids,
        domains=domains,
        start_at=campaign.start_at
    )
    
    # Store messages
    campaign_store.create_messages(messages)
    
    # Update campaign status
    campaign_store.update_campaign_status(campaign.id, CampaignStatus.running)
    
    logger.info(f"Started campaign {campaign.id} with {len(messages)} messages")
