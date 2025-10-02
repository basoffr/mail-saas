from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any, List
import logging

from app.core.auth import require_auth
from app.core.templates_store import get_all_templates, get_template, get_templates_summary
from app.schemas.common import DataResponse
from app.schemas.template import (
    TemplateOut, TemplateDetail, TemplatePreviewResponse, 
    TestsendPayload, TemplatesResponse, TemplateVarItem
)
from app.services.template_renderer import render_template_with_lead
from app.services.testsend import testsend_service
from app.services.leads_store import leads_store
from app.services.template_variables import template_variables_service

router = APIRouter(prefix="/templates", tags=["templates"])
logger = logging.getLogger(__name__)




@router.get("", response_model=DataResponse[TemplatesResponse])
async def list_templates(
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get list of all hard-coded templates (read-only)"""
    try:
        templates = get_all_templates()
        
        template_outs = [
            TemplateOut(
                id=t.id,
                name=f"V{t.version} Mail {t.mail_number}",
                subject_template=t.subject,
                updated_at="2025-09-26T00:00:00Z",  # Hard-coded timestamp
                required_vars=t.placeholders
            )
            for t in templates.values()
        ]
        
        logger.info("hard_coded_templates_listed", extra={"user": user.get("sub"), "count": len(templates)})
        
        return DataResponse(
            data=TemplatesResponse(items=template_outs, total=len(templates)),
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error listing hard-coded templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{template_id}", response_model=DataResponse[TemplateDetail])
async def get_template_detail(
    template_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get detailed hard-coded template information (read-only)"""
    try:
        template = get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Hard-coded assets (dashboard image)
        assets = [{"key": "dashboard", "type": "image"}]
        
        # Extract variables from template placeholders and convert to TemplateVarItem
        placeholder_strings = template.get_placeholders()
        variables = []
        for placeholder in placeholder_strings:
            # Determine source based on prefix
            if placeholder.startswith('lead.'):
                source = 'lead'
                example = 'Example Company' if 'company' in placeholder else 'https://example.com'
            elif placeholder.startswith('vars.'):
                source = 'vars'
                example = 'example value'
            elif placeholder.startswith('image.'):
                source = 'image'
                example = 'cid:image123'
            else:
                source = 'campaign'
                example = 'example'
            
            variables.append(TemplateVarItem(
                key=placeholder,
                required=True,
                source=source,
                example=example
            ))
        
        detail = TemplateDetail(
            id=template.id,
            name=f"V{template.version} Mail {template.mail_number}",
            subject_template=template.subject,
            body_template=template.body,
            updated_at="2025-09-26T00:00:00Z",  # Hard-coded timestamp
            required_vars=template.placeholders,
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
        template = get_template(template_id)
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
        
        # Extract mail number from template_id (e.g., v1m3 -> 3)
        import re
        mail_number = 1  # default
        match = re.search(r'm(\d)$', template_id)
        if match:
            mail_number = int(match.group(1))
        
        # Render template
        result = render_template_with_lead(
            template.body,
            template.subject,
            lead_data,
            {'name': 'Preview Campaign', 'sender_name': 'Preview Sender'},
            mail_number=mail_number
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


@router.get("/{template_id}/variables", response_model=DataResponse[List[TemplateVarItem]])
async def get_template_variables(
    template_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get template variables list"""
    try:
        template = get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Extract variables from template placeholders
        placeholder_strings = template.get_placeholders()
        variables = []
        for placeholder in placeholder_strings:
            # Determine source based on prefix
            if placeholder.startswith('lead.'):
                source = 'lead'
                example = 'Example Company' if 'company' in placeholder else 'https://example.com'
            elif placeholder.startswith('vars.'):
                source = 'vars'
                example = 'example value'
            elif placeholder.startswith('image.'):
                source = 'image'
                example = 'cid:image123'
            else:
                source = 'campaign'
                example = 'example'
            
            variables.append(TemplateVarItem(
                key=placeholder,
                required=True,
                source=source,
                example=example
            ))
        
        logger.info("template_variables_requested", extra={"user": user.get("sub"), "template_id": template_id})
        
        return DataResponse(data=variables, error=None)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template variables: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{template_id}/testsend", response_model=DataResponse[Dict[str, Any]])
async def send_test_email(
    template_id: str,
    payload: TestsendPayload,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Send test email"""
    try:
        template = get_template(template_id)
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


@router.get("/variables/all")
async def get_all_template_variables(
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get all unique variables from all templates (aggregated)."""
    try:
        all_vars = template_variables_service.get_all_required_variables()
        categorized = template_variables_service.get_categorized_variables()
        
        response = {
            "all_variables": sorted(list(all_vars)),
            "total": len(all_vars),
            "categorized": categorized
        }
        
        logger.info("all_template_variables_requested", extra={
            "user": user.get("sub"),
            "total_vars": len(all_vars)
        })
        
        return DataResponse(data=response, error=None)
        
    except Exception as e:
        logger.error(f"Error getting all template variables: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Block editing endpoints - templates are hard-coded
@router.post("")
async def create_template_forbidden():
    """POST method not allowed - templates are hard-coded"""
    raise HTTPException(
        status_code=405,
        detail={"error": "templates_hard_coded"}
    )


@router.put("/{template_id}")
async def update_template_forbidden(template_id: str):
    """PUT method not allowed - templates are hard-coded"""
    raise HTTPException(
        status_code=405,
        detail={"error": "templates_hard_coded"}
    )


@router.patch("/{template_id}")
async def patch_template_forbidden(template_id: str):
    """PATCH method not allowed - templates are hard-coded"""
    raise HTTPException(
        status_code=405,
        detail={"error": "templates_hard_coded"}
    )


@router.delete("/{template_id}")
async def delete_template_forbidden(template_id: str):
    """DELETE method not allowed - templates are hard-coded"""
    raise HTTPException(
        status_code=405,
        detail={"error": "templates_hard_coded"}
    )
