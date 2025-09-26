from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
import logging

from app.core.auth import require_auth
from app.schemas.common import DataResponse
from app.schemas.template import (
    TemplateOut, TemplateDetail, TemplatePreviewResponse, 
    TestsendPayload, TemplatesResponse
)
from app.services.template_store import template_store
from app.services.template_renderer import render_template_with_lead
from app.services.testsend import testsend_service
from app.services.leads_store import leads_store

router = APIRouter(prefix="/templates", tags=["templates"])
logger = logging.getLogger(__name__)


@router.get("", response_model=DataResponse[TemplatesResponse])
async def list_templates(
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get list of all templates"""
    try:
        templates = template_store.get_all()
        
        template_outs = [
            TemplateOut(
                id=t.id,
                name=t.name,
                subject_template=t.subject_template,
                updated_at=t.updated_at,
                required_vars=t.required_vars
            )
            for t in templates
        ]
        
        logger.info("template_list_requested", extra={"user": user.get("sub"), "count": len(templates)})
        
        return DataResponse(
            data=TemplatesResponse(items=template_outs, total=len(templates)),
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{template_id}", response_model=DataResponse[TemplateDetail])
async def get_template_detail(
    template_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get detailed template information"""
    try:
        template = template_store.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Extract variables from template
        variables = template_store.extract_variables(template)
        
        # Convert assets
        assets = []
        if template.assets:
            for asset in template.assets:
                assets.append({
                    "key": asset["key"],
                    "type": asset["type"]
                })
        
        detail = TemplateDetail(
            id=template.id,
            name=template.name,
            subject_template=template.subject_template,
            body_template=template.body_template,
            updated_at=template.updated_at,
            required_vars=template.required_vars,
            assets=assets,
            variables=variables
        )
        
        logger.info("template_detail_requested", extra={"user": user.get("sub"), "template_id": template_id})
        
        return DataResponse(data=detail, error=None)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template detail: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{template_id}/preview", response_model=DataResponse[TemplatePreviewResponse])
async def preview_template(
    template_id: str,
    lead_id: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Preview template with lead data"""
    try:
        template = template_store.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Get lead data if provided
        lead_data = {}
        warnings = []
        if lead_id:
            lead = leads_store.get_by_id(lead_id)
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
            
            # Check lead status
            if lead.status in ['suppressed', 'bounced']:
                warnings.append(f"Warning: Lead status is '{lead.status}'")
            
            lead_data = {
                'id': lead.id,
                'email': lead.email,
                'company': lead.company,
                'url': lead.url,
                'domain': lead.domain,
                'image_key': lead.image_key,
                'vars': lead.vars
            }
        else:
            # Use dummy lead data for preview
            lead_data = {
                'id': 'preview-lead',
                'email': 'preview@example.com',
                'company': 'Preview Company',
                'url': 'https://preview.com',
                'domain': 'preview.com',
                'image_key': 'preview-image',
                'vars': {
                    'industry': 'Technology',
                    'company_size': '50',
                    'estimated_savings': '5000'
                }
            }
            warnings = ["Using dummy data for preview"]
        
        # Render template
        result = render_template_with_lead(
            template.body_template,
            template.subject_template,
            lead_data,
            {'name': 'Preview Campaign', 'sender_name': 'Preview Sender'}
        )
        
        # Combine warnings
        all_warnings = warnings + (result.get('warnings') or [])
        
        preview_response = TemplatePreviewResponse(
            html=result['html'],
            text=result['text'],
            warnings=all_warnings if all_warnings else None
        )
        
        logger.info("template_preview_requested", extra={
            "user": user.get("sub"), 
            "template_id": template_id, 
            "lead_id": lead_id,
            "warnings_count": len(all_warnings)
        })
        
        if all_warnings:
            logger.info("template_preview_warned", extra={
                "user": user.get("sub"),
                "template_id": template_id,
                "warnings": all_warnings
            })
        
        return DataResponse(data=preview_response, error=None)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{template_id}/testsend", response_model=DataResponse[Dict[str, Any]])
async def send_test_email(
    template_id: str,
    payload: TestsendPayload,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Send test email"""
    try:
        template = template_store.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Get lead data if provided
        lead_data = {}
        if payload.leadId:
            lead = leads_store.get_by_id(payload.leadId)
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
            
            lead_data = {
                'id': lead.id,
                'email': lead.email,
                'company': lead.company,
                'url': lead.url,
                'domain': lead.domain,
                'image_key': lead.image_key,
                'vars': lead.vars
            }
        else:
            # Use dummy lead data
            lead_data = {
                'id': 'test-lead',
                'email': str(payload.to),
                'company': 'Test Company',
                'url': 'https://test.com',
                'domain': 'test.com',
                'image_key': 'test-image',
                'vars': {
                    'industry': 'Technology',
                    'company_size': '25',
                    'estimated_savings': '3000'
                }
            }
        
        # Render template
        result = render_template_with_lead(
            template.body_template,
            template.subject_template,
            lead_data,
            {'name': 'Test Campaign', 'sender_name': 'Test Sender'}
        )
        
        logger.info("template_testsend_requested", extra={
            "user": user.get("sub"),
            "template_id": template_id,
            "to_email": str(payload.to),
            "lead_id": payload.leadId
        })
        
        # Send email
        send_result = await testsend_service.send_test_email(
            to_email=str(payload.to),
            subject=result.get('subject', template.name),
            html_body=result['html'],
            text_body=result['text'],
            user_id=user.get("sub", "default")
        )
        
        if send_result['success']:
            logger.info("template_testsend_sent", extra={
                "user": user.get("sub"),
                "template_id": template_id,
                "to_email": str(payload.to)
            })
            
            return DataResponse(
                data={"ok": True, "message": send_result['message']},
                error=None
            )
        else:
            logger.error("template_testsend_failed", extra={
                "user": user.get("sub"),
                "template_id": template_id,
                "to_email": str(payload.to),
                "error": send_result['error']
            })
            
            return DataResponse(
                data=None,
                error=send_result['error']
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
