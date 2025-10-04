"""PostgreSQL-based template store using Supabase."""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)


class DBTemplateStore:
    """Database template store for production."""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.warning("Supabase credentials not found, DB template store disabled")
            return
        
        try:
            self.supabase = create_client(url, key)
            logger.info("Supabase template store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all templates from database."""
        if not self.supabase:
            logger.warning("Supabase not initialized")
            return []
        
        try:
            response = self.supabase.table('templates').select('*').execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching templates: {e}")
            return []
    
    def get_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID from database."""
        if not self.supabase:
            logger.warning("Supabase not initialized")
            return None
        
        try:
            response = self.supabase.table('templates').select('*').eq('id', template_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching template {template_id}: {e}")
            return None
    
    def get_templates_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all templates for UI."""
        templates = self.get_all()
        summaries = []
        
        for template in templates:
            # Extract version and mail number from ID (e.g., v1m1 -> version=1, mail_number=1)
            template_id = template.get('id', '')
            version = int(template_id[1]) if len(template_id) >= 2 else 0
            mail_number = int(template_id[3]) if len(template_id) >= 4 else 0
            
            summaries.append({
                "id": template_id,
                "version": version,
                "mail_number": mail_number,
                "name": template.get('name', ''),
                "subject": template.get('subject_template', ''),
                "body_preview": (template.get('body_template', '')[:100] + "...") 
                                if len(template.get('body_template', '')) > 100 
                                else template.get('body_template', ''),
                "placeholders": template.get('required_vars', []),
                "assets": template.get('assets', {}),
                "updated_at": template.get('updated_at', '')
            })
        
        return sorted(summaries, key=lambda x: (x["version"], x["mail_number"]))
    
    def get_template_for_flow(self, version: int, mail_number: int) -> Optional[Dict[str, Any]]:
        """Get specific template for version and mail number."""
        template_id = f"v{version}m{mail_number}"
        return self.get_by_id(template_id)
    
    def validate_template_id(self, template_id: str) -> bool:
        """Validate if template ID exists in database."""
        return self.get_by_id(template_id) is not None


# Global instance
db_template_store = DBTemplateStore()
