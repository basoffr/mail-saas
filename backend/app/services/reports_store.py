import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from app.models.report import Report, ReportLink, ReportType
from app.schemas.report import ReportsQuery, ReportOut, ReportDetail


class ReportsStore:
    """In-memory store for reports and report links (MVP implementation)."""
    
    def __init__(self):
        self.reports: Dict[str, Report] = {}
        self.report_links: Dict[str, ReportLink] = {}
    
    
    def create_report(self, report_data: Dict[str, Any]) -> Report:
        """Create a new report."""
        report_id = str(uuid.uuid4())
        report = Report(
            id=report_id,
            **report_data
        )
        self.reports[report_id] = report
        return report
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """Get report by ID."""
        return self.reports.get(report_id)
    
    def list_reports(self, query: ReportsQuery) -> Tuple[List[ReportOut], int]:
        """List reports with filtering and pagination."""
        reports = list(self.reports.values())
        
        # Apply filters
        if query.types:
            reports = [r for r in reports if r.type in query.types]
        
        if query.search:
            search_lower = query.search.lower()
            reports = [r for r in reports if search_lower in r.filename.lower()]
        
        # Filter by bound status
        if query.bound_filter:
            if query.bound_filter == "bound":
                bound_report_ids = {link.report_id for link in self.report_links.values()}
                reports = [r for r in reports if r.id in bound_report_ids]
            elif query.bound_filter == "unbound":
                bound_report_ids = {link.report_id for link in self.report_links.values()}
                reports = [r for r in reports if r.id not in bound_report_ids]
        
        # Sort by created_at desc
        reports.sort(key=lambda r: r.created_at, reverse=True)
        
        total = len(reports)
        
        # Pagination
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        reports = reports[start:end]
        
        # Convert to output format with bound_to info
        report_outs = []
        for report in reports:
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
        
        return report_outs, total
    
    def get_report_detail(self, report_id: str) -> Optional[ReportDetail]:
        """Get detailed report info."""
        report = self.reports.get(report_id)
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
        # Remove existing links for this report (MVP: 1:1 relationship)
        self._remove_links_for_report(report_id)
        
        link_id = str(uuid.uuid4())
        link = ReportLink(
            id=link_id,
            report_id=report_id,
            lead_id=lead_id,
            campaign_id=campaign_id,
            created_at=datetime.utcnow()
        )
        self.report_links[link_id] = link
        return link
    
    def remove_links_for_report(self, report_id: str) -> int:
        """Remove all links for a report."""
        return self._remove_links_for_report(report_id)
    
    def _remove_links_for_report(self, report_id: str) -> int:
        """Internal method to remove links for a report."""
        links_to_remove = [
            link_id for link_id, link in self.report_links.items()
            if link.report_id == report_id
        ]
        
        for link_id in links_to_remove:
            del self.report_links[link_id]
        
        return len(links_to_remove)
    
    def _get_bound_to_info(self, report_id: str) -> Optional[Dict[str, str]]:
        """Get bound_to information for a report."""
        for link in self.report_links.values():
            if link.report_id == report_id:
                if link.lead_id:
                    # In real implementation, we'd fetch lead details
                    return {
                        "kind": "lead",
                        "id": link.lead_id,
                        "label": f"Lead {link.lead_id}"  # Simplified for MVP
                    }
                elif link.campaign_id:
                    # In real implementation, we'd fetch campaign details
                    return {
                        "kind": "campaign", 
                        "id": link.campaign_id,
                        "label": f"Campaign {link.campaign_id}"  # Simplified for MVP
                    }
        return None
    
    def get_report_for_lead(self, lead_id: str) -> Optional[Report]:
        """Get report linked to a specific lead."""
        for link in self.report_links.values():
            if link.lead_id == lead_id:
                return self.reports.get(link.report_id)
        return None
    
    def get_report_for_campaign(self, campaign_id: str) -> Optional[Report]:
        """Get report linked to a specific campaign."""
        for link in self.report_links.values():
            if link.campaign_id == campaign_id:
                return self.reports.get(link.report_id)
        return None


# Global instance
reports_store = ReportsStore()
