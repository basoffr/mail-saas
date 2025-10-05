"""
Bulk Import API - Upload Leads + Screenshots + Reports in één keer
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.core.auth import require_auth
from app.services.bulk_import import bulk_import_service
from app.schemas.common import DataResponse


router = APIRouter(dependencies=[Depends(require_auth)])


class BulkImportResult(BaseModel):
    leads_imported: int
    screenshots_uploaded: int
    reports_uploaded: int
    leads_complete: int
    warnings: list[str] = []


@router.post("/bulk-import", response_model=DataResponse[BulkImportResult])
async def bulk_import(
    excel_file: UploadFile = File(..., description="Excel bestand met leads + variabelen"),
    list_name: str = Form(..., description="Naam voor deze import batch"),
    screenshots_zip: Optional[UploadFile] = File(None, description="ZIP met screenshots (optioneel)"),
    reports_zip: Optional[UploadFile] = File(None, description="ZIP met reports (optioneel)"),
):
    """
    Bulk import: Upload leads + screenshots + reports in één keer
    
    **Flow:**
    1. Upload screenshots ZIP → Supabase Storage
    2. Upload reports ZIP → Supabase Storage  
    3. Parse Excel → Extract leads + variabelen
    4. Auto-link screenshot + report per lead (via normalized domain)
    5. Bulk insert leads naar database
    
    **Excel Format:**
    Verwachte kolommen:
    - email (required)
    - domain (required)
    - company / Bedrijfsnaam
    - url (optional)
    - keyword / Keyword
    - google_rank / Google Rank
    - city / plaats
    - phone / telefoon
    
    **Normalized Domain Matching:**
    - Excel: "labelnoir.nl" → normalized: "labelnoir"
    - Screenshot: "labelnoir_40e03960.png" → normalized: "labelnoir"
    - Report: "labelnoir_report.pdf" → normalized: "labelnoir"
    - → Auto-linked! ✅
    """
    try:
        # Validate Excel file
        if not excel_file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Excel file (.xlsx or .xls) required."
            )
        
        # Validate ZIP files if provided
        if screenshots_zip and not screenshots_zip.filename.endswith('.zip'):
            raise HTTPException(
                status_code=400,
                detail="Screenshots must be a ZIP file"
            )
        
        if reports_zip and not reports_zip.filename.endswith('.zip'):
            raise HTTPException(
                status_code=400,
                detail="Reports must be a ZIP file"
            )
        
        # Process bulk import
        result = await bulk_import_service.process_bulk_import(
            excel_file=excel_file,
            screenshots_zip=screenshots_zip,
            reports_zip=reports_zip,
            list_name=list_name
        )
        
        return {
            "data": result,
            "error": None
        }
        
    except Exception as e:
        return {
            "data": None,
            "error": str(e)
        }


class ClearDataResponse(BaseModel):
    success: bool
    message: str


@router.post("/clear-all-data", response_model=DataResponse[ClearDataResponse])
async def clear_all_data():
    """
    ⚠️ DANGER: Verwijder ALLE data uit Supabase
    
    Gebruik alleen voor clean slate imports.
    Verwijdert:
    - Alle leads
    - Alle reports
    - Alle report_links
    - Alle assets
    """
    try:
        await bulk_import_service.clear_all_data()
        
        return {
            "data": {
                "success": True,
                "message": "All data cleared successfully"
            },
            "error": None
        }
    except Exception as e:
        return {
            "data": None,
            "error": str(e)
        }


@router.get("/lists", response_model=DataResponse[list[str]])
async def get_lists():
    """
    Get alle unieke lijst namen uit de database
    
    Voor gebruik in Campaign Wizard om een lijst te selecteren
    """
    try:
        import os
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            # Fallback to mock data
            return {
                "data": ["Q4 2024 Batch", "Test Batch"],
                "error": None
            }
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Query distinct list_name from leads table
        response = supabase.table('leads').select('list_name').execute()
        
        # Extract unique non-null list names
        list_names = set()
        for row in response.data:
            if row.get('list_name'):
                list_names.add(row['list_name'])
        
        return {
            "data": sorted(list(list_names)),
            "error": None
        }
    except Exception as e:
        return {
            "data": None,
            "error": str(e)
        }
