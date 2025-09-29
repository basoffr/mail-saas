from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models.template import Template
from app.schemas.template import TemplateVarItem


class TemplateStore:
    """In-memory template store for MVP"""
    
    def __init__(self):
        self.templates: Dict[str, Template] = {}
    
    
    def get_all(self) -> List[Template]:
        """Get all templates"""
        return list(self.templates.values())
    
    def get_by_id(self, template_id: str) -> Optional[Template]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def extract_variables(self, template: Template) -> List[TemplateVarItem]:
        """Extract variable information from template"""
        from app.services.template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        
        # Extract from both subject and body
        subject_vars = renderer.extract_variables(template.subject_template)
        body_vars = renderer.extract_variables(template.body_template)
        
        all_vars = list(set(subject_vars + body_vars))
        
        variables = []
        for var in all_vars:
            var = var.strip()
            
            # Determine source and required status
            if var.startswith('lead.'):
                source = 'lead'
                required = var in ['lead.email', 'lead.company']
            elif var.startswith('vars.'):
                source = 'vars'
                required = var in template.required_vars
            elif var.startswith('campaign.'):
                source = 'campaign'
                required = False
            elif var.startswith('image.'):
                source = 'image'
                required = 'cid' in var  # CID images are per-lead, required
            else:
                source = 'unknown'
                required = False
            
            # Generate example
            example = self._generate_example(var, source)
            
            variables.append(TemplateVarItem(
                key=var,
                required=required,
                source=source,
                example=example
            ))
        
        return variables
    
    def _generate_example(self, var: str, source: str) -> Optional[str]:
        """Generate example value for variable"""
        examples = {
            'lead.email': 'john.doe@example.com',
            'lead.company': 'Acme Corporation',
            'lead.url': 'https://acme.com',
            'vars.industry': 'Technology',
            'vars.company_size': '50',
            'vars.estimated_savings': '5000',
            'campaign.name': 'Q4 Outreach Campaign',
            'campaign.sender_name': 'Sarah Johnson'
        }
        
        return examples.get(var)


# Global instance
template_store = TemplateStore()
