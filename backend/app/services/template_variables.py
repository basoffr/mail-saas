"""
Template Variables Service - Aggregeert alle variabelen uit templates.

Dit service scant alle hard-coded templates en bepaalt:
- Welke variabelen er in totaal gebruikt worden
- Welke variabelen een specifieke lead mist
- De compleetheid score van een lead
"""

from typing import Set, List, Dict, Any, Optional
import re
from app.core.templates_store import get_all_templates
from app.models.lead import Lead


class TemplateVariablesService:
    """Service voor template variabelen aggregatie en lead compleetheid."""
    
    def __init__(self):
        self._cached_variables: Optional[Set[str]] = None
    
    def get_all_required_variables(self) -> Set[str]:
        """
        Aggregeer alle unieke variabelen uit alle 16 templates.
        
        Returns:
            Set van variabele names, bijv:
            {'lead.company', 'lead.url', 'vars.keyword', 'vars.google_rank', 'image.cid'}
        """
        if self._cached_variables is not None:
            return self._cached_variables
        
        all_variables: Set[str] = set()
        templates = get_all_templates()
        
        # Pattern voor {{variable}} extractie
        pattern = r'\{\{([^}]+)\}\}'
        
        for template_id, template in templates.items():
            # Scan subject en body
            content = template.subject + " " + template.body
            matches = re.findall(pattern, content)
            
            for match in matches:
                var = match.strip()
                
                # Normaliseer variabele namen
                if var.startswith('lead.'):
                    all_variables.add(var)
                elif var.startswith('vars.'):
                    all_variables.add(var)
                elif var.startswith('campaign.'):
                    all_variables.add(var)
                elif 'image.cid' in var:
                    # Alle image.cid variaties tellen als 1 type
                    all_variables.add('image.cid')
                elif var.startswith('image.'):
                    all_variables.add(var)
        
        self._cached_variables = all_variables
        return all_variables
    
    def get_categorized_variables(self) -> Dict[str, List[str]]:
        """
        Categoriseer variabelen per type.
        
        Returns:
            Dict met categorieën:
            {
                'lead_fields': ['lead.company', 'lead.url'],
                'custom_vars': ['vars.keyword', 'vars.google_rank'],
                'images': ['image.cid'],
                'campaign': []
            }
        """
        all_vars = self.get_all_required_variables()
        
        categorized = {
            'lead_fields': [],
            'custom_vars': [],
            'images': [],
            'campaign': []
        }
        
        for var in sorted(all_vars):
            if var.startswith('lead.'):
                categorized['lead_fields'].append(var)
            elif var.startswith('vars.'):
                categorized['custom_vars'].append(var)
            elif var.startswith('image.'):
                categorized['images'].append(var)
            elif var.startswith('campaign.'):
                categorized['campaign'].append(var)
        
        return categorized
    
    def get_missing_variables(self, lead: Lead) -> List[str]:
        """
        Bepaal welke variabelen een lead mist.
        
        Args:
            lead: Lead object met vars dict en image_key
            
        Returns:
            List van ontbrekende variabele namen
        """
        required_vars = self.get_all_required_variables()
        missing = []
        
        for var in sorted(required_vars):
            if var.startswith('lead.'):
                # Check lead field
                field_name = var.split('.', 1)[1]
                if not hasattr(lead, field_name) or not getattr(lead, field_name):
                    missing.append(var)
            
            elif var.startswith('vars.'):
                # Check custom var in vars dict
                var_name = var.split('.', 1)[1]
                if not lead.vars or var_name not in lead.vars or not lead.vars[var_name]:
                    missing.append(var)
            
            elif var == 'image.cid':
                # Check image_key
                if not lead.image_key:
                    missing.append(var)
            
            # campaign.* vars worden niet gecheckt (runtime data)
        
        return missing
    
    def calculate_completeness(self, lead: Lead) -> Dict[str, Any]:
        """
        Bereken compleetheid score van een lead.
        
        Campaign V1 vereist 5 template variables:
        - vars.keyword
        - vars.seo_score
        - vars.google_rank
        - vars.report_filename
        - image (via image_key, gebruikt als {{image.cid}} in templates)
        
        Args:
            lead: Lead object
            
        Returns:
            Dict met:
            {
                'filled': 4,
                'total': 5,
                'missing': ['vars.google_rank'],
                'percentage': 80,
                'is_complete': False
            }
        """
        # Campaign V1 requirements: 5 template variables
        required_vars_in_dict = ['keyword', 'seo_score', 'google_rank', 'report_filename']
        
        missing = []
        filled_count = 0
        
        # Check 4 required vars in lead.vars
        for var_name in required_vars_in_dict:
            if lead.vars and var_name in lead.vars and lead.vars[var_name]:
                filled_count += 1
            else:
                missing.append(f'vars.{var_name}')
        
        # Check image (5th variable, stored in image_key field)
        if lead.image_key and lead.image_key != '':
            filled_count += 1
        else:
            missing.append('image')
        
        total = 5  # Always 5 template variables for Campaign V1
        
        return {
            'filled': filled_count,
            'total': total,
            'missing': missing,
            'percentage': int((filled_count / total * 100)),
            'is_complete': filled_count == 5
        }
    
    def get_variable_value(self, lead: Lead, var_name: str) -> Optional[str]:
        """
        Haal de waarde van een variabele op voor een lead.
        
        Args:
            lead: Lead object
            var_name: Variabele naam (bijv 'lead.company' of 'vars.keyword')
            
        Returns:
            String waarde of None
        """
        if var_name.startswith('lead.'):
            field = var_name.split('.', 1)[1]
            return str(getattr(lead, field, '')) if hasattr(lead, field) else None
        
        elif var_name.startswith('vars.'):
            var_key = var_name.split('.', 1)[1]
            if lead.vars and var_key in lead.vars:
                return str(lead.vars[var_key])
            return None
        
        elif var_name == 'image.cid':
            return lead.image_key if lead.image_key else None
        
        return None


# Global singleton instance
template_variables_service = TemplateVariablesService()
