from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse

from app.core.auth import require_auth
from app.schemas.common import DataResponse
from app.schemas.stats import StatsSummary, StatsQuery
from app.services.stats import stats_service

router = APIRouter()




@router.get("/summary", response_model=DataResponse[StatsSummary])
async def get_stats_summary(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    template_id: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get comprehensive statistics summary"""
    try:
        # Parse dates
        parsed_from = None
        parsed_to = None
        
        if from_date:
            try:
                parsed_from = datetime.fromisoformat(from_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from date format. Use YYYY-MM-DD")
        
        if to_date:
            try:
                parsed_to = datetime.fromisoformat(to_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to date format. Use YYYY-MM-DD")
        
        # Validate date range
        if parsed_from and parsed_to:
            if parsed_from > parsed_to:
                raise HTTPException(status_code=400, detail="From date must be before or equal to to date")
            
            # Max 365 days range
            if (parsed_to - parsed_from).days > 365:
                raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
        
        # Default to last 30 days if no dates provided
        if not parsed_from and not parsed_to:
            parsed_to = date.today()
            parsed_from = parsed_to - timedelta(days=30)
        
        # Get statistics
        summary = stats_service.get_stats_summary(
            from_date=parsed_from,
            to_date=parsed_to,
            template_id=template_id
        )
        
        return DataResponse(data=summary, error=None)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/export")
async def export_stats(
    scope: str = Query(..., pattern="^(global|domain|campaign)$"),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    id: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Export statistics as CSV"""
    try:
        # Parse dates
        parsed_from = None
        parsed_to = None
        
        if from_date:
            try:
                parsed_from = datetime.fromisoformat(from_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from date format. Use YYYY-MM-DD")
        
        if to_date:
            try:
                parsed_to = datetime.fromisoformat(to_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to date format. Use YYYY-MM-DD")
        
        # Validate date range
        if parsed_from and parsed_to:
            if parsed_from > parsed_to:
                raise HTTPException(status_code=400, detail="From date must be before or equal to to date")
            
            if (parsed_to - parsed_from).days > 365:
                raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
        
        # Default to last 30 days if no dates provided
        if not parsed_from and not parsed_to:
            parsed_to = date.today()
            parsed_from = parsed_to - timedelta(days=30)
        
        # Generate CSV
        csv_content = stats_service.export_csv(
            scope=scope,
            from_date=parsed_from,
            to_date=parsed_to,
            entity_id=id
        )
        
        # Generate filename
        date_suffix = f"{parsed_from}_{parsed_to}" if parsed_from and parsed_to else "all"
        filename = f"stats_{scope}_{date_suffix}.csv"
        
        return PlainTextResponse(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export statistics: {str(e)}")


@router.get("/domains", response_model=DataResponse[list])
async def get_domain_stats(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get domain statistics (optional endpoint)"""
    try:
        # Parse dates (same logic as summary)
        parsed_from = None
        parsed_to = None
        
        if from_date:
            parsed_from = datetime.fromisoformat(from_date).date()
        if to_date:
            parsed_to = datetime.fromisoformat(to_date).date()
        
        if not parsed_from and not parsed_to:
            parsed_to = date.today()
            parsed_from = parsed_to - timedelta(days=30)
        
        # Get full summary and extract domains
        summary = stats_service.get_stats_summary(
            from_date=parsed_from,
            to_date=parsed_to
        )
        
        return DataResponse(data=summary.domains, error=None)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get domain statistics: {str(e)}")


@router.get("/campaigns", response_model=DataResponse[list])
async def get_campaign_stats(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get campaign statistics (optional endpoint)"""
    try:
        # Parse dates (same logic as summary)
        parsed_from = None
        parsed_to = None
        
        if from_date:
            parsed_from = datetime.fromisoformat(from_date).date()
        if to_date:
            parsed_to = datetime.fromisoformat(to_date).date()
        
        if not parsed_from and not parsed_to:
            parsed_to = date.today()
            parsed_from = parsed_to - timedelta(days=30)
        
        # Get full summary and extract campaigns
        summary = stats_service.get_stats_summary(
            from_date=parsed_from,
            to_date=parsed_to
        )
        
        return DataResponse(data=summary.campaigns, error=None)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get campaign statistics: {str(e)}")
