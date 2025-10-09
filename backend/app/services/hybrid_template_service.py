"""
Hybrid Template Service
Provides database-first template access with hard-coded fallback.
"""
import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from app.core.templates_store import (
    HardCodedTemplate,
    get_template as get_hardcoded_template,
    get_all_templates as get_all_hardcoded_templates,
    get_templates_for_version as get_hardcoded_templates_for_version
)
from app.services.db_template_store import DBTemplateStore

logger = logging.getLogger(__name__)


class HybridTemplateService:
    """
    Hybrid Template Service: Database-first with hard-coded fallback.
    
    Flow:
    1. Try to fetch template from database (Supabase)
    2. If not found or error, fall back to hard-coded templates
    3. Return unified HardCodedTemplate object
    
    This ensures zero downtime even if database is unavailable.
    """
    
    def __init__(self):
        self.db_store = DBTemplateStore()
        self._use_db = os.getenv('USE_IN_MEMORY_STORES', 'true').lower() == 'false'
        logger.info(f"HybridTemplateService initialized (use_db={self._use_db})")
    
    def get_template(self, template_id: str) -> Optional[HardCodedTemplate]:
        """
        Get template by ID (normalized).
        
        Tries database first, then falls back to hard-coded.
        
        Args:
            template_id: Normalized template ID (e.g., v1_mail1)
        
        Returns:
            HardCodedTemplate object or None if not found
        """
        # Try database first (if enabled)
        if self._use_db:
            db_template = self._get_from_database(template_id)
            if db_template:
                logger.info(f"[HYBRID] ✅ Template '{template_id}' found in database")
                return db_template
            logger.info(f"[HYBRID] ⚠️  Template '{template_id}' not in database, trying fallback")
        
        # Fallback to hard-coded
        hardcoded_template = get_hardcoded_template(template_id)
        if hardcoded_template:
            logger.info(f"[HYBRID] ✅ Template '{template_id}' found in hard-coded store")
            return hardcoded_template
        
        logger.warning(f"[HYBRID] ❌ Template '{template_id}' not found anywhere")
        return None
    
    def get_all_templates(self) -> List[HardCodedTemplate]:
        """
        Get all templates (merged from DB + hard-coded).
        
        Database templates override hard-coded ones with same ID.
        
        Returns:
            List of HardCodedTemplate objects
        """
        templates_dict: Dict[str, HardCodedTemplate] = {}
        
        # Start with hard-coded (baseline)
        hardcoded = get_all_hardcoded_templates()
        for template_id, template in hardcoded.items():
            templates_dict[template_id] = template
        
        # Override with database templates (if enabled)
        if self._use_db:
            db_templates = self.db_store.get_all()
            for db_row in db_templates:
                template_id = db_row.get('id')
                if template_id:
                    db_template = self._db_row_to_template(db_row)
                    if db_template:
                        templates_dict[template_id] = db_template
                        logger.debug(f"[HYBRID] Database template '{template_id}' overrides hard-coded")
        
        return list(templates_dict.values())
    
    def get_templates_by_version(self, version: int) -> List[HardCodedTemplate]:
        """
        Get all templates for specific version (1-4).
        
        Args:
            version: Version number (1, 2, 3, or 4)
        
        Returns:
            List of HardCodedTemplate objects for that version
        """
        all_templates = self.get_all_templates()
        return [t for t in all_templates if t.version == version]
    
    def get_template_for_flow(self, version: int, mail_number: int) -> Optional[HardCodedTemplate]:
        """
        Get specific template for version and mail number.
        
        Args:
            version: Version number (1-4)
            mail_number: Mail number (1-4)
        
        Returns:
            HardCodedTemplate or None
        """
        template_id = f"v{version}_mail{mail_number}"
        return self.get_template(template_id)
    
    def _get_from_database(self, template_id: str) -> Optional[HardCodedTemplate]:
        """
        Get template from database and convert to HardCodedTemplate.
        
        Args:
            template_id: Template ID
        
        Returns:
            HardCodedTemplate or None
        """
        try:
            db_row = self.db_store.get_by_id(template_id)
            if not db_row:
                return None
            
            return self._db_row_to_template(db_row)
            
        except Exception as e:
            logger.error(f"[HYBRID] Database error for '{template_id}': {e}, falling back to hard-coded")
            return None
    
    def _db_row_to_template(self, db_row: Dict[str, Any]) -> Optional[HardCodedTemplate]:
        """
        Convert database row to HardCodedTemplate object.
        
        Args:
            db_row: Database row dict
        
        Returns:
            HardCodedTemplate or None if conversion fails
        """
        try:
            template_id = db_row.get('id')
            
            # Extract version and mail_number from ID or fields
            version = db_row.get('version')
            mail_number = db_row.get('mail_number')
            
            # If not in DB row, parse from ID (v1_mail1 -> version=1, mail_number=1)
            if version is None or mail_number is None:
                import re
                match = re.match(r'v(\d+)_mail(\d+)', template_id)
                if match:
                    version = int(match.group(1))
                    mail_number = int(match.group(2))
                else:
                    logger.warning(f"[HYBRID] Cannot parse version/mail_number from ID '{template_id}'")
                    return None
            
            # Get required vars (may be list or None)
            required_vars = db_row.get('required_vars', [])
            if required_vars is None:
                required_vars = []
            
            return HardCodedTemplate(
                id=template_id,
                version=int(version),
                mail_number=int(mail_number),
                subject=db_row.get('subject_template', ''),
                body=db_row.get('body_template', ''),
                placeholders=required_vars
            )
            
        except Exception as e:
            logger.error(f"[HYBRID] Error converting DB row to template: {e}")
            return None


# Global instance
hybrid_template_service = HybridTemplateService()
