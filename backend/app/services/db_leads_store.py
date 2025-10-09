"""PostgreSQL-based leads store using Supabase."""
import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from supabase import create_client, Client
import logging
import json

from app.schemas.lead import LeadOut, LeadDetail, LeadStatus

logger = logging.getLogger(__name__)


class DBLeadsStore:
    """Database leads store for production using Supabase."""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.warning("Supabase credentials not found, DB leads store disabled")
            return
        
        try:
            self.supabase = create_client(url, key)
            logger.info("Supabase leads store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
    
    def _row_to_lead(self, row: Dict[str, Any]) -> LeadOut:
        """Convert database row to LeadOut."""
        # Parse vars JSON string to dict
        vars_data = row.get('vars', {})
        if isinstance(vars_data, str):
            try:
                vars_data = json.loads(vars_data)
            except:
                vars_data = {}
        
        # Parse tags JSON string to list
        tags_data = row.get('tags', [])
        if isinstance(tags_data, str):
            try:
                tags_data = json.loads(tags_data)
            except:
                tags_data = []
        
        return LeadOut(
            id=row['id'],
            email=row['email'],
            company=row.get('company'),
            url=row.get('url'),
            domain=row.get('domain'),
            status=LeadStatus(row.get('status', 'active')),
            tags=tags_data,
            image_key=row.get('image_key'),
            list_name=row.get('list_name'),
            last_emailed_at=row.get('last_emailed_at'),
            last_open_at=row.get('last_open_at'),
            vars=vars_data,
            stopped=row.get('stopped', False),
            deleted_at=row.get('deleted_at'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            is_deleted=row.get('deleted_at') is not None,
        )
    
    def query(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None,
        status: Optional[LeadStatus] = None,
        tags: Optional[List[str]] = None,
        has_image: Optional[bool] = None,
        has_vars: Optional[bool] = None,
        list_name: Optional[str] = None,
        is_complete: Optional[bool] = None,
        tld: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        include_deleted: bool = False,
    ) -> Tuple[List[LeadOut], int]:
        """Query leads with filters and pagination.
        
        NOTE: Supabase has a 1000 row limit per .range() call.
        If page_size > 1000, we automatically fetch in batches.
        """
        if not self.supabase:
            logger.warning("Supabase not initialized")
            return [], 0
        
        try:
            # Build base query with filters
            def build_query():
                q = self.supabase.table('leads').select('*', count='exact')
                
                # Filter out deleted unless explicitly requested
                if not include_deleted:
                    q = q.is_('deleted_at', 'null')
                
                # Apply filters
                if search:
                    q = q.or_(f'email.ilike.%{search}%,company.ilike.%{search}%,domain.ilike.%{search}%')
                
                if status:
                    q = q.eq('status', status.value)
                
                if list_name:
                    q = q.eq('list_name', list_name)
                
                if tld:
                    q = q.ilike('domain', f'%.{tld}')
                
                if has_image is not None:
                    if has_image:
                        q = q.not_.is_('image_key', 'null')
                    else:
                        q = q.is_('image_key', 'null')
                
                # Sorting
                if sort_by:
                    ascending = (sort_order != 'desc')
                    q = q.order(sort_by, desc=not ascending)
                else:
                    q = q.order('created_at', desc=True)
                
                return q
            
            # Supabase range() has max 1000 rows per call
            SUPABASE_MAX_ROWS = 1000
            
            if page_size <= SUPABASE_MAX_ROWS:
                # Simple case: single query
                query = build_query()
                start = (page - 1) * page_size
                end = start + page_size - 1
                query = query.range(start, end)
                
                response = query.execute()
                leads = [self._row_to_lead(row) for row in (response.data or [])]
                total = response.count or 0
            else:
                # Complex case: fetch in batches of 1000
                logger.info(f"Large page_size ({page_size}) detected, fetching in batches...")
                all_leads = []
                total = 0
                batch_num = 0
                
                # Calculate how many batches we need
                start_offset = (page - 1) * page_size
                remaining = page_size
                
                while remaining > 0:
                    batch_size = min(remaining, SUPABASE_MAX_ROWS)
                    batch_start = start_offset + (batch_num * SUPABASE_MAX_ROWS)
                    batch_end = batch_start + batch_size - 1
                    
                    logger.info(f"Fetching batch {batch_num + 1}: rows {batch_start}-{batch_end}")
                    
                    query = build_query()
                    query = query.range(batch_start, batch_end)
                    response = query.execute()
                    
                    batch_leads = [self._row_to_lead(row) for row in (response.data or [])]
                    all_leads.extend(batch_leads)
                    
                    # Total count is same for all batches
                    if batch_num == 0:
                        total = response.count or 0
                    
                    # If we got fewer rows than requested, we've hit the end
                    if len(batch_leads) < batch_size:
                        break
                    
                    remaining -= batch_size
                    batch_num += 1
                
                leads = all_leads
                logger.info(f"Fetched {len(leads)} leads in {batch_num + 1} batches (total available: {total})")
            
            return leads, total
            
        except Exception as e:
            logger.error(f"Error querying leads: {e}")
            return [], 0
    
    def get_by_id(self, lead_id: str) -> Optional[LeadOut]:
        """Get lead by ID."""
        if not self.supabase:
            logger.warning("Supabase not initialized")
            return None
        
        try:
            response = self.supabase.table('leads').select('*').eq('id', lead_id).execute()
            if response.data and len(response.data) > 0:
                return self._row_to_lead(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching lead {lead_id}: {e}")
            return None
    
    def get_by_email(self, email: str) -> Optional[LeadOut]:
        """Get lead by email."""
        if not self.supabase:
            logger.warning("Supabase not initialized")
            return None
        
        try:
            response = self.supabase.table('leads').select('*').eq('email', email).execute()
            if response.data and len(response.data) > 0:
                return self._row_to_lead(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching lead by email {email}: {e}")
            return None
    
    def get_all(self) -> List[LeadOut]:
        """Get all leads (non-deleted)."""
        leads, _ = self.query(page=1, page_size=10000, include_deleted=False)
        return leads
    
    def upsert(
        self,
        *,
        email: str,
        company: Optional[str] = None,
        url: Optional[str] = None,
        domain: Optional[str] = None,
        status: LeadStatus = LeadStatus.active,
        tags: Optional[List[str]] = None,
        image_key: Optional[str] = None,
        list_name: Optional[str] = None,
        vars: Optional[dict] = None,
        stopped: bool = False,
    ) -> LeadOut:
        """Upsert a lead."""
        # Implementation would use Supabase upsert
        # For now, simplified version
        existing = self.get_by_email(email)
        
        data = {
            'email': email,
            'company': company,
            'url': url,
            'domain': domain,
            'status': status.value,
            'tags': json.dumps(tags or []),
            'image_key': image_key,
            'list_name': list_name,
            'vars': json.dumps(vars or {}),
            'stopped': stopped,
            'updated_at': datetime.utcnow().isoformat(),
        }
        
        if existing:
            # Update
            data['id'] = existing.id
        else:
            # Insert
            import hashlib
            lead_id = f"lead_{hashlib.md5(email.encode()).hexdigest()[:12]}"
            data['id'] = lead_id
            data['created_at'] = datetime.utcnow().isoformat()
        
        try:
            response = self.supabase.table('leads').upsert(data).execute()
            if response.data and len(response.data) > 0:
                return self._row_to_lead(response.data[0])
        except Exception as e:
            logger.error(f"Error upserting lead: {e}")
        
        return None
