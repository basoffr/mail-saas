"""PostgreSQL-based campaign store using Supabase."""
import os
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from supabase import create_client, Client
import logging
import json

from app.models.campaign import Campaign, CampaignAudience, Message, MessageEvent, CampaignStatus, MessageStatus
from app.schemas.campaign import CampaignQuery, MessageQuery, CampaignKPIs, TimelinePoint

logger = logging.getLogger(__name__)


class DBCampaignStore:
    """Database campaign store for production using Supabase."""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.warning("Supabase credentials not found, DB campaign store disabled")
            return
        
        try:
            self.supabase = create_client(url, key)
            logger.info("Supabase campaign store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
    
    def _row_to_campaign(self, row: Dict[str, Any]) -> Campaign:
        """Convert database row to Campaign."""
        return Campaign(
            id=row['id'],
            name=row['name'],
            template_id=row['template_id'],
            domain=row['domain'],
            status=CampaignStatus(row.get('status', 'draft')),
            start_at=row.get('start_at'),
            followup_enabled=row.get('followup_enabled', False),
            followup_days=row.get('followup_days', 3),
            followup_attach_report=row.get('followup_attach_report', False),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
    
    def _row_to_audience(self, row: Dict[str, Any]) -> CampaignAudience:
        """Convert database row to CampaignAudience."""
        # Parse lead_ids JSON
        lead_ids = row.get('lead_ids', [])
        if isinstance(lead_ids, str):
            try:
                lead_ids = json.loads(lead_ids)
            except:
                lead_ids = []
        
        return CampaignAudience(
            id=row['id'],
            campaign_id=row['campaign_id'],
            lead_ids=lead_ids,
            exclude_suppressed=row.get('exclude_suppressed', True),
            exclude_recent_days=row.get('exclude_recent_days', 90),
            one_per_domain=row.get('one_per_domain', True),
            created_at=row.get('created_at'),
        )
    
    def _row_to_message(self, row: Dict[str, Any]) -> Message:
        """Convert database row to Message."""
        return Message(
            id=row['id'],
            campaign_id=row['campaign_id'],
            lead_id=row['lead_id'],
            domain_used=row['domain_used'],
            template_version=row.get('template_version', 1),
            is_followup=row.get('is_followup', False),
            scheduled_at=row['scheduled_at'],
            sent_at=row.get('sent_at'),
            status=MessageStatus(row.get('status', 'pending')),
            last_error=row.get('last_error'),
            attempts=row.get('attempts', 0),
            open_at=row.get('open_at'),
            reply_at=row.get('reply_at'),
            created_at=row.get('created_at'),
        )
    
    def create_campaign(self, campaign: Campaign) -> Campaign:
        """Create a new campaign."""
        if not self.supabase:
            logger.error("Supabase not initialized")
            raise Exception("Database not available")
        
        try:
            data = {
                "id": campaign.id,
                "name": campaign.name,
                "template_id": campaign.template_id,
                "domain": campaign.domain,
                "status": campaign.status.value,
                "start_at": campaign.start_at.isoformat() if campaign.start_at else None,
                "followup_enabled": campaign.followup_enabled,
                "followup_days": campaign.followup_days,
                "followup_attach_report": campaign.followup_attach_report,
                "created_at": campaign.created_at.isoformat() if campaign.created_at else datetime.utcnow().isoformat(),
                "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else datetime.utcnow().isoformat(),
            }
            
            response = self.supabase.table("campaigns").insert(data).execute()
            logger.info(f"Created campaign {campaign.id}: {campaign.name}")
            return campaign
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise
    
    def duplicate_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Duplicate an existing campaign with new ID and reset status."""
        original = self.get_campaign(campaign_id)
        if not original:
            logger.warning(f"Campaign {campaign_id} not found for duplication")
            return None
        
        # Create new campaign with copied attributes
        new_id = str(uuid.uuid4())
        duplicate = Campaign(
            id=new_id,
            name=f"{original.name} (Copy)",
            template_id=original.template_id,
            domain=original.domain,
            status=CampaignStatus.draft,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            start_at=None,  # Reset start date
            followup_enabled=original.followup_enabled,
            followup_days=original.followup_days,
            followup_attach_report=original.followup_attach_report
        )
        
        # Save duplicate
        self.create_campaign(duplicate)
        logger.info(f"Duplicated campaign {campaign_id} to {new_id}: {duplicate.name}")
        
        # Copy audience if exists
        original_audience = self.get_audience(campaign_id)
        if original_audience:
            new_audience = CampaignAudience(
                id=str(uuid.uuid4()),
                campaign_id=new_id,
                lead_ids=original_audience.lead_ids.copy(),
                exclude_suppressed=original_audience.exclude_suppressed,
                exclude_recent_days=original_audience.exclude_recent_days,
                one_per_domain=original_audience.one_per_domain,
                created_at=datetime.utcnow()
            )
            self.create_audience(new_audience)
            logger.info(f"Duplicated audience with {len(new_audience.lead_ids)} leads")
        
        return duplicate
    
    def check_domain_busy(self, domain: str) -> bool:
        """Check if domain has an active campaign running."""
        if not self.supabase:
            return False
        
        try:
            response = self.supabase.table("campaigns")\
                .select("id")\
                .eq("domain", domain)\
                .eq("status", CampaignStatus.running.value)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking domain busy: {e}")
            return False
    
    def get_active_campaigns_by_domain(self) -> Dict[str, List[Campaign]]:
        """Get all active campaigns grouped by domain."""
        if not self.supabase:
            return {}
        
        try:
            response = self.supabase.table("campaigns")\
                .select("*")\
                .eq("status", CampaignStatus.running.value)\
                .execute()
            
            domain_campaigns = {}
            for row in response.data:
                campaign = self._row_to_campaign(row)
                if campaign.domain not in domain_campaigns:
                    domain_campaigns[campaign.domain] = []
                domain_campaigns[campaign.domain].append(campaign)
            
            return domain_campaigns
            
        except Exception as e:
            logger.error(f"Error getting active campaigns by domain: {e}")
            return {}
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages for CSV export."""
        if not self.supabase:
            return []
        
        try:
            # Fetch in batches due to Supabase 1000 row limit
            all_messages = []
            offset = 0
            batch_size = 1000
            
            while True:
                response = self.supabase.table("messages")\
                    .select("*")\
                    .range(offset, offset + batch_size - 1)\
                    .execute()
                
                if not response.data:
                    break
                
                for row in response.data:
                    all_messages.append(self._row_to_message(row))
                
                if len(response.data) < batch_size:
                    break
                
                offset += batch_size
            
            return all_messages
            
        except Exception as e:
            logger.error(f"Error getting all messages: {e}")
            return []
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("campaigns")\
                .select("*")\
                .eq("id", campaign_id)\
                .execute()
            
            if response.data:
                return self._row_to_campaign(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting campaign: {e}")
            return None
    
    def list_campaigns(self, query: CampaignQuery) -> Tuple[List[Campaign], int]:
        """List campaigns with filtering and pagination."""
        if not self.supabase:
            return [], 0
        
        try:
            # Build query
            db_query = self.supabase.table("campaigns").select("*", count="exact")
            
            # Apply filters
            if query.status:
                status_values = [s.value for s in query.status]
                db_query = db_query.in_("status", status_values)
            
            if query.search:
                db_query = db_query.ilike("name", f"%{query.search}%")
            
            if query.date_from:
                db_query = db_query.gte("created_at", query.date_from.isoformat())
            
            if query.date_to:
                db_query = db_query.lte("created_at", query.date_to.isoformat())
            
            # Sort and paginate
            db_query = db_query.order("created_at", desc=True)
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size - 1
            db_query = db_query.range(start, end)
            
            # Execute
            response = db_query.execute()
            
            campaigns = [self._row_to_campaign(row) for row in response.data]
            total = response.count if hasattr(response, 'count') else len(campaigns)
            
            return campaigns, total
            
        except Exception as e:
            logger.error(f"Error listing campaigns: {e}")
            return [], 0
    
    def update_campaign_status(self, campaign_id: str, status: CampaignStatus) -> bool:
        """Update campaign status."""
        if not self.supabase:
            return False
        
        try:
            self.supabase.table("campaigns")\
                .update({
                    "status": status.value,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", campaign_id)\
                .execute()
            
            logger.info(f"Updated campaign {campaign_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating campaign status: {e}")
            return False
    
    def create_audience(self, audience: CampaignAudience) -> CampaignAudience:
        """Create campaign audience snapshot."""
        if not self.supabase:
            raise Exception("Database not available")
        
        try:
            data = {
                "id": audience.id,
                "campaign_id": audience.campaign_id,
                "lead_ids": json.dumps(audience.lead_ids),
                "exclude_suppressed": audience.exclude_suppressed,
                "exclude_recent_days": audience.exclude_recent_days,
                "one_per_domain": audience.one_per_domain,
                "created_at": audience.created_at.isoformat() if audience.created_at else datetime.utcnow().isoformat(),
            }
            
            self.supabase.table("campaign_audience").insert(data).execute()
            return audience
            
        except Exception as e:
            logger.error(f"Error creating audience: {e}")
            raise
    
    def get_audience(self, campaign_id: str) -> Optional[CampaignAudience]:
        """Get audience for campaign."""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("campaign_audience")\
                .select("*")\
                .eq("campaign_id", campaign_id)\
                .execute()
            
            if response.data:
                return self._row_to_audience(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting audience: {e}")
            return None
    
    def create_messages(self, messages: List[Message]) -> List[Message]:
        """Create multiple messages."""
        if not self.supabase:
            raise Exception("Database not available")
        
        try:
            data_list = []
            for message in messages:
                data_list.append({
                    "id": message.id,
                    "campaign_id": message.campaign_id,
                    "lead_id": message.lead_id,
                    "domain_used": message.domain_used,
                    "template_version": message.template_version,
                    "is_followup": message.is_followup,
                    "scheduled_at": message.scheduled_at.isoformat(),
                    "status": message.status.value,
                    "attempts": message.attempts,
                    "created_at": message.created_at.isoformat() if message.created_at else datetime.utcnow().isoformat(),
                })
            
            self.supabase.table("messages").insert(data_list).execute()
            logger.info(f"Created {len(messages)} messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error creating messages: {e}")
            raise
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID."""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("messages")\
                .select("*")\
                .eq("id", message_id)\
                .execute()
            
            if response.data:
                return self._row_to_message(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting message: {e}")
            return None
    
    def list_messages(self, query: MessageQuery) -> Tuple[List[Message], int]:
        """List messages with filtering and pagination."""
        if not self.supabase:
            return [], 0
        
        try:
            # Build query
            db_query = self.supabase.table("messages").select("*", count="exact")
            
            # Apply filters
            if query.campaign_id:
                db_query = db_query.eq("campaign_id", query.campaign_id)
            
            if query.status:
                status_values = [s.value for s in query.status]
                db_query = db_query.in_("status", status_values)
            
            if query.lead_id:
                db_query = db_query.eq("lead_id", query.lead_id)
            
            # Sort and paginate
            db_query = db_query.order("scheduled_at", desc=False)
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size - 1
            db_query = db_query.range(start, end)
            
            # Execute
            response = db_query.execute()
            
            messages = [self._row_to_message(row) for row in response.data]
            total = response.count if hasattr(response, 'count') else len(messages)
            
            return messages, total
            
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            return [], 0
    
    def update_message_status(self, message_id: str, status: MessageStatus, error: str = None) -> bool:
        """Update message status."""
        if not self.supabase:
            return False
        
        try:
            update_data = {
                "status": status.value,
            }
            
            if status == MessageStatus.sent:
                update_data["sent_at"] = datetime.utcnow().isoformat()
            
            if error:
                update_data["last_error"] = error
            
            self.supabase.table("messages")\
                .update(update_data)\
                .eq("id", message_id)\
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating message status: {e}")
            return False
    
    def create_event(self, event: MessageEvent) -> MessageEvent:
        """Create message event."""
        if not self.supabase:
            raise Exception("Database not available")
        
        try:
            data = {
                "id": event.id,
                "message_id": event.message_id,
                "event_type": event.event_type.value,
                "created_at": event.created_at.isoformat() if event.created_at else datetime.utcnow().isoformat(),
            }
            
            self.supabase.table("message_events").insert(data).execute()
            return event
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise
    
    def get_campaign_kpis(self, campaign_id: str) -> CampaignKPIs:
        """Calculate campaign KPIs."""
        if not self.supabase:
            return CampaignKPIs(
                total_planned=0,
                total_sent=0,
                total_opened=0,
                total_failed=0,
                open_rate=0.0,
                avg_tempo_per_hour=0.0
            )
        
        try:
            # Get all messages for campaign
            response = self.supabase.table("messages")\
                .select("status")\
                .eq("campaign_id", campaign_id)\
                .execute()
            
            messages = response.data
            total_planned = len(messages)
            total_sent = len([m for m in messages if m['status'] == MessageStatus.sent.value])
            total_opened = len([m for m in messages if m['status'] == MessageStatus.opened.value])
            total_failed = len([m for m in messages if m['status'] == MessageStatus.failed.value])
            
            open_rate = (total_opened / total_sent) if total_sent > 0 else 0.0
            avg_tempo_per_hour = 3.0  # 1 email per 20 min = 3 per hour per domain
            
            return CampaignKPIs(
                total_planned=total_planned,
                total_sent=total_sent,
                total_opened=total_opened,
                total_failed=total_failed,
                open_rate=open_rate,
                avg_tempo_per_hour=avg_tempo_per_hour
            )
            
        except Exception as e:
            logger.error(f"Error getting campaign KPIs: {e}")
            return CampaignKPIs(
                total_planned=0,
                total_sent=0,
                total_opened=0,
                total_failed=0,
                open_rate=0.0,
                avg_tempo_per_hour=0.0
            )
    
    def get_campaign_timeline(self, campaign_id: str) -> List[TimelinePoint]:
        """Get campaign timeline data."""
        if not self.supabase:
            return []
        
        try:
            # Get all sent messages for campaign
            response = self.supabase.table("messages")\
                .select("sent_at, status")\
                .eq("campaign_id", campaign_id)\
                .not_.is_("sent_at", "null")\
                .execute()
            
            # Group by date
            daily_stats: Dict[str, Dict[str, int]] = {}
            
            for message in response.data:
                if message.get('sent_at'):
                    # Parse ISO datetime
                    sent_at = datetime.fromisoformat(message['sent_at'].replace('Z', '+00:00'))
                    date_key = sent_at.strftime("%Y-%m-%d")
                    
                    if date_key not in daily_stats:
                        daily_stats[date_key] = {"sent": 0, "opened": 0}
                    
                    daily_stats[date_key]["sent"] += 1
                    
                    if message.get('status') == MessageStatus.opened.value:
                        daily_stats[date_key]["opened"] += 1
            
            # Convert to timeline points
            timeline = []
            for date, stats in sorted(daily_stats.items()):
                timeline.append(TimelinePoint(
                    date=date,
                    sent=stats["sent"],
                    opened=stats["opened"]
                ))
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting campaign timeline: {e}")
            return []
