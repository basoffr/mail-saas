"""
Admin API - Endpoints voor administratieve taken
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from loguru import logger
from typing import List, Dict, Any
from app.schemas.common import DataResponse
from app.services.store_factory import leads_store
from app.core.auth import require_auth

router = APIRouter(tags=["admin"])


@router.get("/audience-by-list", response_model=DataResponse[Dict[str, Any]])
async def get_audience_by_list_name(
    list_name: str = Query(..., description="List name to get audience for"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get campaign audience by list name.
    
    Returns lead IDs that match filters for campaign audience:
    - List name matches
    - Status is 'active'
    - Not stopped
    - Not deleted
    - Has report (vars.report_filename exists)
    - Has image (image_key exists)
    
    This is used to build campaign audiences from lead lists.
    
    Args:
        list_name: Name of the list (e.g., "Webshop Campaign V1")
    
    Returns:
        {
            "list_name": str,
            "total_in_list": int,
            "eligible_count": int,
            "lead_ids": List[str],
            "filters_applied": {
                "status": "active",
                "stopped": false,
                "deleted": false,
                "has_report": true,
                "has_image": true
            }
        }
    """
    try:
        # Get all leads from the list
        # query() returns (List[LeadOut], int) tuple
        # Set page_size=999999 to get ALL leads (bypass pagination)
        all_leads, _ = leads_store.query(
            list_name=list_name,
            include_deleted=False,  # Exclude deleted leads
            page_size=999999  # Get ALL leads, not just first page
        )
        
        total_in_list = len(all_leads)
        
        # Filter leads for campaign eligibility
        eligible_leads = []
        for lead in all_leads:
            # Must be active
            if lead.status != "active":
                continue
            
            # Must not be stopped
            if lead.stopped:
                continue
            
            # Must have report
            if not lead.vars or not lead.vars.get("report_filename"):
                continue
            
            # Must have image
            if not lead.image_key:
                continue
            
            eligible_leads.append(lead)
        
        lead_ids = [lead.id for lead in eligible_leads]
        
        logger.info(
            f"Audience for '{list_name}': "
            f"{len(lead_ids)} eligible / {total_in_list} total"
        )
        
        return DataResponse(data={
            "list_name": list_name,
            "total_in_list": total_in_list,
            "eligible_count": len(lead_ids),
            "lead_ids": lead_ids,
            "filters_applied": {
                "status": "active",
                "stopped": False,
                "deleted": False,
                "has_report": True,
                "has_image": True
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get audience for list '{list_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get audience: {str(e)}"
        )


@router.get("/list-names", response_model=DataResponse[List[str]])
async def get_list_names(user: Dict[str, Any] = Depends(require_auth)):
    """
    Get all unique list names in the database.
    
    Returns:
        List of unique list_name values
    """
    try:
        # Get all leads
        # query() returns (List[LeadOut], int) tuple
        # Set page_size=999999 to get ALL leads (bypass pagination)
        all_leads, _ = leads_store.query(
            include_deleted=False,
            page_size=999999  # Get ALL leads, not just first page
        )
        
        # Extract unique list names
        list_names = set()
        for lead in all_leads:
            if lead.list_name:
                list_names.add(lead.list_name)
        
        sorted_list_names = sorted(list(list_names))
        
        logger.info(f"Found {len(sorted_list_names)} unique list names")
        
        return DataResponse(data=sorted_list_names)
        
    except Exception as e:
        logger.error(f"Failed to get list names: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get list names: {str(e)}"
        )
