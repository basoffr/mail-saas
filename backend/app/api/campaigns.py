import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger
from app.core.auth import require_auth
from app.core.campaign_flows import get_all_flows, get_flow_for_domain
from app.schemas.common import DataResponse
from app.schemas.campaign import (
    CampaignOut, CampaignDetail, CampaignCreatePayload, CampaignsResponse,
    MessageOut, MessagesResponse, CampaignActionResponse, DryRunResponse,
    ResendPayload, CampaignQuery, MessageQuery,
    CampaignControlResponse, StopLeadRequest, StopLeadResponse, 
    ScheduleResponse, ScheduledMessageOut
)
from app.models.campaign import Campaign, CampaignAudience, CampaignStatus, MessageStatus
from app.services.store_factory import campaigns_store as campaign_store, leads_store
from app.services.campaign_scheduler import CampaignScheduler
from app.services.message_sender import MessageSender

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
        
        # Enrich campaigns with count fields
        enriched_campaigns = []
        for c in campaigns:
            # Get message counts for this campaign
            messages, _ = campaign_store.list_messages(MessageQuery(campaign_id=c.id, page_size=10000))
            
            # Calculate counts
            target_count = len(messages)
            sent_count = len([m for m in messages if m.sent_at is not None])
            open_count = len([m for m in messages if m.open_at is not None])
            bounce_count = len([m for m in messages if m.status == MessageStatus.bounced])
            
            # Create enriched campaign dict
            campaign_dict = c.__dict__.copy()
            campaign_dict.update({
                'target_count': target_count,
                'sent_count': sent_count,
                'open_count': open_count,
                'click_count': 0,  # Not implemented yet
                'bounce_count': bounce_count,
                'reply_count': 0,  # Not implemented yet
            })
            enriched_campaigns.append(CampaignOut.model_validate(campaign_dict))
        
        response = CampaignsResponse(
            items=enriched_campaigns,
            total=total
        )
        
        logger.info(f"Listed {len(campaigns)} campaigns (total: {total})")
        return DataResponse(data=response)
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _assign_next_available_flow(start_at: Optional[datetime] = None):
    """Assign next available flow/domain (round-robin).
    
    Returns:
        tuple: (flow, domain, templates)
    
    Raises:
        HTTPException: If all domains are busy
    """
    flows = get_all_flows()
    check_time = start_at or datetime.now()
    
    # Try each flow/domain in order (v1-v4)
    for domain, flow in flows.items():
        if not campaign_store.check_domain_busy(domain):
            # Get templates for this flow version
            templates = [
                f"v{flow.version}m1",
                f"v{flow.version}m2",
                f"v{flow.version}m3",
                f"v{flow.version}m4"
            ]
            return flow, domain, templates
    
    # All domains busy
    raise HTTPException(
        status_code=409,
        detail={"error": "all_domains_busy", "message": "All domains are currently running campaigns"}
    )


@router.post("", response_model=DataResponse[Dict[str, str]])
async def create_campaign(
    payload: CampaignCreatePayload,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create a new campaign with auto-assigned flow/domain/templates."""
    try:
        # Auto-assign flow/domain/templates (round-robin first available)
        flow, domain, templates = _assign_next_available_flow(payload.schedule.start_at)
        
        logger.info(
            f"Auto-assigned: flow v{flow.version} ({domain}), "
            f"templates: {templates}"
        )
        
        # Template ID is nullable - templates are determined per message, not per campaign
        # The campaign uses templates array stored in detail response
        template_id = None  # Templates handled at message level
        
        # Create campaign with auto-assigned values
        campaign = Campaign(
            id=str(uuid.uuid4()),
            name=payload.name,
            template_id=template_id,  # Nullable - templates per message
            domain=domain,
            start_at=payload.schedule.start_at if payload.schedule.start_mode == "scheduled" else None,
            status=CampaignStatus.draft,
            followup_enabled=True,  # Hard-coded
            followup_days=3,  # Hard-coded: +3 workdays
            followup_attach_report=False  # Hard-coded for MVP
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
        
        # V2.2: ALWAYS create and schedule messages at campaign creation
        # This makes the schedule timeline immediately visible
        if payload.schedule.start_mode == "now":
            # Start immediately: scheduler determines next available slot
            await _start_campaign(campaign, audience, [domain], start_now=True)
        else:
            # Start scheduled: use provided start_at date
            await _start_campaign(campaign, audience, [domain], start_now=False)
        
        logger.info(f"Created campaign {campaign.id}: {campaign.name} with {len(audience.lead_ids)} leads scheduled")
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
        
        # Auto-assigned fields (for simplified flow)
        # These are derived/hardcoded values, not stored in DB
        flow_version = 1  # Default flow version
        templates = ["v1m1", "v1m2", "v1m3", "v1m4"]  # Standard 4-template flow
        estimated_duration_days = 9  # Standard 9 workdays
        
        detail = CampaignDetail(
            **campaign.__dict__,
            kpis=kpis,
            timeline=timeline,
            domains_used=domains_used,
            audience_count=audience_count,
            flow_version=flow_version,
            templates=templates,
            estimated_duration_days=estimated_duration_days
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


@router.post("/{campaign_id}/duplicate", response_model=DataResponse[CampaignOut])
async def duplicate_campaign(
    campaign_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Duplicate an existing campaign with new ID."""
    try:
        # Check if campaign exists
        original = campaign_store.get_campaign(campaign_id)
        if not original:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Duplicate campaign
        duplicate = campaign_store.duplicate_campaign(campaign_id)
        if not duplicate:
            raise HTTPException(status_code=500, detail="Failed to duplicate campaign")
        
        logger.info(f"Duplicated campaign {campaign_id} to {duplicate.id}")
        
        # Return duplicated campaign
        return DataResponse(
            data=CampaignOut.model_validate(duplicate.__dict__)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating campaign: {str(e)}")
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


@router.get("/{campaign_id}/messages", response_model=DataResponse[MessagesResponse])
async def get_campaign_messages(
    campaign_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: List[MessageStatus] = Query(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get messages for a specific campaign."""
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
        logger.error(f"Error getting campaign messages: {str(e)}")
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


# V2.2: Campaign Controls
@router.delete("/{campaign_id}", response_model=DataResponse[CampaignControlResponse])
async def delete_campaign(
    campaign_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """V2.2: Soft delete campaign and cancel future messages (admin only)."""
    try:
        # TODO: Add RBAC check for admin role
        # if user.get("role") != "admin":
        #     raise HTTPException(status_code=403, detail="Admin only")
        
        success = campaign_store.soft_delete_campaign(campaign_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        logger.info(f"Soft deleted campaign {campaign_id} by user {user.get('sub')}")
        return DataResponse(data=CampaignControlResponse(ok=True, message="Campaign deleted"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{campaign_id}/pause", response_model=DataResponse[CampaignControlResponse])
async def pause_campaign(
    campaign_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """V2.2: Pause campaign (admin only)."""
    try:
        # TODO: Add RBAC check for admin role
        
        success = campaign_store.pause_campaign(campaign_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        logger.info(f"Paused campaign {campaign_id}")
        return DataResponse(data=CampaignControlResponse(ok=True, message="Campaign paused"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{campaign_id}/resume", response_model=DataResponse[CampaignControlResponse])
async def resume_campaign(
    campaign_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """V2.2: Resume paused campaign (admin only)."""
    try:
        # TODO: Add RBAC check for admin role
        
        success = campaign_store.resume_campaign(campaign_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found or not paused")
        
        logger.info(f"Resumed campaign {campaign_id}")
        return DataResponse(data=CampaignControlResponse(ok=True, message="Campaign resumed"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{campaign_id}/leads/{lead_id}/stop", response_model=DataResponse[StopLeadResponse])
async def stop_lead_flow(
    campaign_id: str,
    lead_id: str,
    request: StopLeadRequest,
    user: Dict[str, Any] = Depends(require_auth)
):
    """V2.2: Stop lead's campaign flow with reason (admin only)."""
    try:
        # TODO: Add RBAC check for admin role
        
        # Validate reason
        if request.reason not in ["unsubscribe", "bounce", "manual"]:
            raise HTTPException(status_code=400, detail="Invalid reason. Must be: unsubscribe, bounce, or manual")
        
        # Update lead flags
        if request.reason == "unsubscribe":
            leads_store.mark_unsubscribed(lead_id)
        elif request.reason == "bounce":
            leads_store.mark_bounced(lead_id)
        # For 'manual', no global lead flags (campaign-scope only)
        
        # Cancel future messages
        result = campaign_store.stop_lead_flow(campaign_id, lead_id, request.reason)
        
        logger.info(f"Stopped lead {lead_id} in campaign {campaign_id}: {result['canceled_count']} messages canceled (reason: {request.reason})")
        
        return DataResponse(data=StopLeadResponse(**result))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping lead flow: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{campaign_id}/schedule", response_model=DataResponse[ScheduleResponse])
async def get_schedule(
    campaign_id: str,
    limit: int = Query(200, ge=1, le=500),
    domain: Optional[str] = Query(None),
    from_ts: Optional[datetime] = Query(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """V2.2: Get campaign scheduling timeline (admin & viewer)."""
    try:
        # Get campaign
        campaign = campaign_store.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get scheduled messages
        messages = campaign_store.get_schedule(
            campaign_id=campaign_id,
            limit=limit,
            domain=domain,
            from_ts=from_ts
        )
        
        # Convert to ScheduledMessageOut
        slots = [
            ScheduledMessageOut(
                message_id=m.id,
                lead_id=m.lead_id,
                mail_number=m.mail_number,
                alias=m.alias,
                domain_used=m.domain_used,
                scheduled_at=m.scheduled_at,
                status=m.status,
                cancel_reason=getattr(m, 'cancel_reason', None)
            )
            for m in messages
        ]
        
        response = ScheduleResponse(
            campaign_id=campaign_id,
            effective_start=campaign.start_at or campaign.created_at,
            slots=slots,
            total_count=len(slots)
        )
        
        logger.info(f"Retrieved schedule for campaign {campaign_id}: {len(slots)} slots")
        return DataResponse(data=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _start_campaign(
    campaign: Campaign, 
    audience: CampaignAudience, 
    domains: List[str],
    start_now: bool = True
):
    """V2.2: Create and schedule messages for campaign.
    
    Args:
        campaign: Campaign object
        audience: Audience with lead_ids
        domains: List of domains to use
        start_now: If True, start immediately (status=active). If False, keep draft status.
    """
    
    # Determine start_at based on mode
    start_at = None if start_now else campaign.start_at
    
    # Create messages with scheduler
    messages = scheduler.create_campaign_messages(
        campaign=campaign,
        lead_ids=audience.lead_ids,
        domains=domains,
        start_at=start_at
    )
    
    # Store messages in database
    campaign_store.create_messages(messages)
    
    # Update campaign status
    if start_now:
        # Starting now: set to active/running
        campaign_store.update_campaign_status(campaign.id, CampaignStatus.active)
        logger.info(f"Started campaign {campaign.id} with {len(messages)} messages (immediate start)")
    else:
        # Scheduled start: keep as draft until start_at
        logger.info(f"Scheduled campaign {campaign.id} with {len(messages)} messages (starts at {campaign.start_at})")
