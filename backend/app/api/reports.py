import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from loguru import logger

from app.core.auth import require_auth
from app.schemas.common import DataResponse
from app.schemas.report import (
    ReportsResponse, ReportsQuery, ReportDetail, ReportBindPayload, 
    ReportUnbindPayload, BulkUploadResult, DownloadResponse
)
from app.services.store_factory import reports_store, leads_store
from app.services.file_handler import file_handler

router = APIRouter(prefix="/reports", tags=["reports"])




@router.get("", response_model=DataResponse[ReportsResponse])
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    types: Optional[str] = Query(None),
    bound_filter: Optional[str] = Query(None),
    bound_kind: Optional[str] = Query(None),
    bound_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """List reports with filtering and pagination."""
    try:
        # Parse types filter
        type_list = None
        if types:
            type_list = [t.strip() for t in types.split(",") if t.strip()]
        
        query = ReportsQuery(
            page=page,
            page_size=page_size,
            types=type_list,
            bound_filter=bound_filter,
            bound_kind=bound_kind,
            bound_id=bound_id,
            search=search,
            date_from=date_from,
            date_to=date_to
        )
        
        reports, total = reports_store.list_reports(query)
        
        response = ReportsResponse(items=reports, total=total)
        
        logger.info(f"Listed {len(reports)} reports (total: {total}) for user {user.get('sub')}")
        
        return DataResponse(data=response, error=None)
    
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{report_id}", response_model=DataResponse[ReportDetail])
async def get_report(
    report_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get detailed report information."""
    try:
        report = reports_store.get_report_detail(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        logger.info(f"Retrieved report {report_id} for user {user.get('sub')}")
        
        return DataResponse(data=report, error=None)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload", response_model=DataResponse[ReportDetail])
async def upload_report(
    file: UploadFile = File(...),
    lead_id: Optional[str] = Form(None),
    campaign_id: Optional[str] = Form(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Upload a single report file."""
    try:
        # Validate that only one of lead_id or campaign_id is provided
        if lead_id and campaign_id:
            raise HTTPException(
                status_code=422, 
                detail="Cannot bind to both lead and campaign"
            )
        
        # Validate file
        file_type = file_handler.validate_file(file)
        
        # Generate report ID
        report_id = str(uuid.uuid4())
        
        # Save file
        storage_path, checksum, size_bytes = await file_handler.save_file(file, report_id)
        
        # Create report record
        report_data = {
            "filename": file.filename or f"report_{report_id}",
            "type": file_type,
            "size_bytes": size_bytes,
            "storage_path": storage_path,
            "checksum": checksum,
            "created_at": datetime.utcnow(),
            "uploaded_by": user.get("sub")
        }
        
        report = reports_store.create_report(report_data)
        
        # Create link if specified
        if lead_id or campaign_id:
            reports_store.create_link(report.id, lead_id=lead_id, campaign_id=campaign_id)
        
        # Get detailed report info
        report_detail = reports_store.get_report_detail(report.id)
        
        logger.info(f"Uploaded report {report.id} ({file.filename}) for user {user.get('sub')}")
        
        return DataResponse(data=report_detail, error=None)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bulk", response_model=DataResponse[BulkUploadResult])
async def bulk_upload_reports(
    file: UploadFile = File(...),
    mode: str = Query(..., pattern="^(by_image_key|by_email)$"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Bulk upload reports from ZIP file."""
    try:
        # Get leads data for mapping
        leads_data = []
        for lead in leads_store._leads:
            leads_data.append({
                "id": lead.id,
                "email": lead.email,
                "image_key": lead.image_key
            })
        
        # Process bulk upload
        result = await file_handler.process_bulk_upload(file, mode, leads_data)
        
        logger.info(f"Bulk upload completed: {result.uploaded} uploaded, {result.failed} failed for user {user.get('sub')}")
        
        return DataResponse(data=result, error=None)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bind", response_model=DataResponse[Dict[str, bool]])
async def bind_report(
    payload: ReportBindPayload,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Bind report to lead or campaign."""
    try:
        # Validate that only one of lead_id or campaign_id is provided
        if payload.lead_id and payload.campaign_id:
            raise HTTPException(
                status_code=422,
                detail="Cannot bind to both lead and campaign"
            )
        
        if not payload.lead_id and not payload.campaign_id:
            raise HTTPException(
                status_code=422,
                detail="Must specify either lead_id or campaign_id"
            )
        
        # Check if report exists
        report = reports_store.get_report(payload.report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Create link
        reports_store.create_link(
            payload.report_id, 
            lead_id=payload.lead_id, 
            campaign_id=payload.campaign_id
        )
        
        logger.info(f"Bound report {payload.report_id} to {'lead' if payload.lead_id else 'campaign'} {payload.lead_id or payload.campaign_id}")
        
        return DataResponse(data={"ok": True}, error=None)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error binding report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/unbind", response_model=DataResponse[Dict[str, bool]])
async def unbind_report(
    payload: ReportUnbindPayload,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Unbind report from lead or campaign."""
    try:
        # Check if report exists
        report = reports_store.get_report(payload.report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Remove links
        removed_count = reports_store.remove_links_for_report(payload.report_id)
        
        logger.info(f"Unbound report {payload.report_id} (removed {removed_count} links)")
        
        return DataResponse(data={"ok": True}, error=None)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unbinding report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{report_id}/download", response_model=DataResponse[DownloadResponse])
async def download_report(
    report_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get download URL for report."""
    try:
        report = reports_store.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Generate signed URL
        download_url = file_handler.generate_download_url(report.storage_path)
        
        response = DownloadResponse(
            url=download_url,
            expires_at=datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        )
        
        logger.info(f"Generated download URL for report {report_id} for user {user.get('sub')}")
        
        return DataResponse(data=response, error=None)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL for report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
