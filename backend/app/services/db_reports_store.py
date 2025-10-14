"""PostgreSQL-based reports store using Supabase."""
import os
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from supabase import create_client, Client
import logging
import json

from app.models.report import Report, ReportLink, ReportType
from app.schemas.report import ReportsQuery, ReportOut, ReportDetail

logger = logging.getLogger(__name__)


class DBReportsStore:
    """Database reports store for production using Supabase."""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.warning("Supabase credentials not found, DB reports store disabled")
            return
        
        try:
            self.supabase = create_client(url, key)
            logger.info("Supabase reports store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
    
    def _row_to_report(self, row: Dict[str, Any]) -> Report:
        """Convert database row to Report."""
        meta_data = row.get('meta')
        if isinstance(meta_data, str):
            try:
                meta_data = json.loads(meta_data)
            except:
                meta_data = None
        
        return Report(
            id=row['id'],
            filename=row['filename'],
            type=ReportType(row['type']),
            size_bytes=row['size_bytes'],
            storage_path=row['storage_path'],
            checksum=row.get('checksum'),
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if isinstance(row['created_at'], str) else row['created_at'],
            uploaded_by=row.get('uploaded_by'),
            meta=meta_data
        )
    
    def create_report(self, report_data: Dict[str, Any]) -> Report:
        """Create a new report."""
        if not self.supabase:
            raise Exception("Supabase not initialized")
        
        try:
            report_id = str(uuid.uuid4())
            insert_data = {
                'id': report_id,
                'filename': report_data['filename'],
                'type': report_data['type'],
                'size_bytes': report_data['size_bytes'],
                'storage_path': report_data['storage_path'],
                'checksum': report_data.get('checksum'),
                'created_at': datetime.utcnow().isoformat(),
                'uploaded_by': report_data.get('uploaded_by'),
                'meta': json.dumps(report_data.get('meta')) if report_data.get('meta') else None
            }
            
            result = self.supabase.table('reports').insert(insert_data).execute()
            return self._row_to_report(result.data[0])
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            raise
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """Get report by ID."""
        if not self.supabase:
            logger.warning("Supabase not initialized")
            return None
        
        try:
            result = self.supabase.table('reports').select('*').eq('id', report_id).execute()
            if result.data:
                return self._row_to_report(result.data[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get report: {e}")
            return None
    
    def list_reports(self, query: ReportsQuery) -> Tuple[List[ReportOut], int]:
        """List reports with filtering and pagination."""
        if not self.supabase:
            logger.warning("Supabase not initialized")
            return [], 0
        
        try:
            # Build query
            supabase_query = self.supabase.table('reports').select('*', count='exact')
            
            # Apply type filter
            if query.types:
                supabase_query = supabase_query.in_('type', query.types)
            
            # Apply search filter (filename or domain/email via leads)
            if query.search:
                search_lower = query.search.lower()
                
                # Search in filename
                supabase_query = supabase_query.or_(f'filename.ilike.%{search_lower}%')
                
                # Also search by domain/email via report_links -> leads
                # This requires a more complex join query
                # For now, we'll do a simple filename search
                # TODO: Add proper join query for domain/email search
            
            # Get count for pagination
            count_result = self.supabase.table('reports').select('*', count='exact', head=True).execute()
            total = count_result.count if count_result.count is not None else 0
            
            # Sort by created_at desc
            supabase_query = supabase_query.order('created_at', desc=True)
            
            # Pagination
            start = (query.page - 1) * query.page_size
            end = start + query.page_size - 1
            supabase_query = supabase_query.range(start, end)
            
            result = supabase_query.execute()
            
            # Convert to output format with bound_to info
            report_outs = []
            for row in result.data:
                report = self._row_to_report(row)
                bound_to = self._get_bound_to_info(report.id)
                
                report_out = ReportOut(
                    id=report.id,
                    filename=report.filename,
                    type=report.type,
                    size_bytes=report.size_bytes,
                    created_at=report.created_at,
                    bound_to=bound_to
                )
                report_outs.append(report_out)
            
            # Apply bound filter
            if query.bound_filter:
                if query.bound_filter == "bound":
                    report_outs = [r for r in report_outs if r.bound_to is not None]
                elif query.bound_filter == "unbound":
                    report_outs = [r for r in report_outs if r.bound_to is None]
                
                total = len(report_outs)
            
            return report_outs, total
        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            return [], 0
    
    def get_report_detail(self, report_id: str) -> Optional[ReportDetail]:
        """Get detailed report info."""
        report = self.get_report(report_id)
        if not report:
            return None
        
        bound_to = self._get_bound_to_info(report_id)
        
        return ReportDetail(
            id=report.id,
            filename=report.filename,
            type=report.type,
            size_bytes=report.size_bytes,
            storage_path=report.storage_path,
            checksum=report.checksum,
            created_at=report.created_at,
            uploaded_by=report.uploaded_by,
            meta=report.meta,
            bound_to=bound_to
        )
    
    def create_link(self, report_id: str, lead_id: Optional[str] = None, 
                   campaign_id: Optional[str] = None) -> ReportLink:
        """Create a link between report and lead/campaign."""
        if not self.supabase:
            raise Exception("Supabase not initialized")
        
        try:
            # Remove existing links for this report (MVP: 1:1 relationship)
            self._remove_links_for_report(report_id)
            
            link_id = str(uuid.uuid4())
            insert_data = {
                'id': link_id,
                'report_id': report_id,
                'lead_id': lead_id,
                'campaign_id': campaign_id,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('report_links').insert(insert_data).execute()
            row = result.data[0]
            
            return ReportLink(
                id=row['id'],
                report_id=row['report_id'],
                lead_id=row.get('lead_id'),
                campaign_id=row.get('campaign_id'),
                created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if isinstance(row['created_at'], str) else row['created_at']
            )
        except Exception as e:
            logger.error(f"Failed to create report link: {e}")
            raise
    
    def remove_links_for_report(self, report_id: str) -> int:
        """Remove all links for a report."""
        return self._remove_links_for_report(report_id)
    
    def _remove_links_for_report(self, report_id: str) -> int:
        """Internal method to remove links for a report."""
        if not self.supabase:
            return 0
        
        try:
            result = self.supabase.table('report_links').delete().eq('report_id', report_id).execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"Failed to remove report links: {e}")
            return 0
    
    def _get_bound_to_info(self, report_id: str) -> Optional[Dict[str, str]]:
        """Get bound_to information for a report."""
        if not self.supabase:
            return None
        
        try:
            # Get link
            link_result = self.supabase.table('report_links').select('*').eq('report_id', report_id).execute()
            
            if not link_result.data:
                return None
            
            link = link_result.data[0]
            
            if link.get('lead_id'):
                # Fetch lead details
                lead_result = self.supabase.table('leads').select('email, company, domain').eq('id', link['lead_id']).execute()
                if lead_result.data:
                    lead = lead_result.data[0]
                    label = lead.get('company') or lead.get('domain') or lead.get('email', f"Lead {link['lead_id']}")
                    return {
                        "kind": "lead",
                        "id": link['lead_id'],
                        "label": label
                    }
            
            elif link.get('campaign_id'):
                # Fetch campaign details
                campaign_result = self.supabase.table('campaigns').select('name').eq('id', link['campaign_id']).execute()
                if campaign_result.data:
                    campaign = campaign_result.data[0]
                    return {
                        "kind": "campaign",
                        "id": link['campaign_id'],
                        "label": campaign.get('name', f"Campaign {link['campaign_id']}")
                    }
            
            return None
        except Exception as e:
            logger.error(f"Failed to get bound_to info: {e}")
            return None
    
    def get_report_for_lead(self, lead_id: str) -> Optional[Report]:
        """Get report linked to a specific lead."""
        if not self.supabase:
            return None
        
        try:
            link_result = self.supabase.table('report_links').select('report_id').eq('lead_id', lead_id).execute()
            
            if not link_result.data:
                return None
            
            report_id = link_result.data[0]['report_id']
            return self.get_report(report_id)
        except Exception as e:
            logger.error(f"Failed to get report for lead: {e}")
            return None
    
    def get_report_for_campaign(self, campaign_id: str) -> Optional[Report]:
        """Get report linked to a specific campaign."""
        if not self.supabase:
            return None
        
        try:
            link_result = self.supabase.table('report_links').select('report_id').eq('campaign_id', campaign_id).execute()
            
            if not link_result.data:
                return None
            
            report_id = link_result.data[0]['report_id']
            return self.get_report(report_id)
        except Exception as e:
            logger.error(f"Failed to get report for campaign: {e}")
            return None
    
    def search_by_domain_or_email(self, search_term: str) -> List[ReportOut]:
        """Search reports by domain or email address via lead links."""
        if not self.supabase:
            logger.warning("Supabase not initialized")
            return []
        
        try:
            search_lower = search_term.lower()
            
            # Search leads by domain or email
            leads_result = self.supabase.table('leads').select('id').or_(
                f'domain.ilike.%{search_lower}%,email.ilike.%{search_lower}%'
            ).execute()
            
            if not leads_result.data:
                return []
            
            lead_ids = [lead['id'] for lead in leads_result.data]
            
            # Get report links for these leads
            links_result = self.supabase.table('report_links').select('report_id').in_('lead_id', lead_ids).execute()
            
            if not links_result.data:
                return []
            
            report_ids = [link['report_id'] for link in links_result.data]
            
            # Get reports
            reports_result = self.supabase.table('reports').select('*').in_('id', report_ids).order('created_at', desc=True).execute()
            
            # Convert to output format
            report_outs = []
            for row in reports_result.data:
                report = self._row_to_report(row)
                bound_to = self._get_bound_to_info(report.id)
                
                report_out = ReportOut(
                    id=report.id,
                    filename=report.filename,
                    type=report.type,
                    size_bytes=report.size_bytes,
                    created_at=report.created_at,
                    bound_to=bound_to
                )
                report_outs.append(report_out)
            
            return report_outs
        except Exception as e:
            logger.error(f"Failed to search reports by domain/email: {e}")
            return []
