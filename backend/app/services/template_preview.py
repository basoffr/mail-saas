from __future__ import annotations
import re
from typing import List, Dict, Any, Set
from html import escape

from app.services.leads_store import LeadsStore
from app.services.template_store import template_store


def extract_template_variables(template_content: str) -> Set[str]:
    """
    Extract all variables from template content.
    Supports patterns like: {{variable}}, {{lead.field}}, {{vars.custom}}, {{image.cid 'key'}}
    """
    # Pattern to match {{variable}} and {{object.property}}
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, template_content)
    
    variables = set()
    for match in matches:
        # Clean up the variable name
        var = match.strip()
        
        # Handle image.cid 'key' pattern
        if var.startswith('image.cid'):
            variables.add('image.cid')
        else:
            variables.add(var)
    
    return variables


def validate_lead_variables(lead: Any, required_vars: Set[str]) -> List[str]:
    """
    Validate that lead has all required variables and return warnings for missing ones.
    """
    warnings = []
    
    for var in required_vars:
        if var.startswith('lead.'):
            # Lead field variable
            field = var.split('.', 1)[1]
            if not hasattr(lead, field) or not getattr(lead, field):
                warnings.append(f"Missing lead field: {field}")
        
        elif var.startswith('vars.'):
            # Custom variable
            var_name = var.split('.', 1)[1]
            if not lead.vars or var_name not in lead.vars or not lead.vars[var_name]:
                warnings.append(f"Missing custom variable: {var_name}")
        
        elif var == 'image.cid':
            # Image CID requirement
            if not lead.image_key:
                warnings.append("Missing image_key for CID images")
        
        elif var in ['firstName', 'companyName', 'industry', 'email']:
            # Common direct variables
            if var == 'firstName':
                # Try to extract from email or check vars
                if not (lead.vars and 'firstName' in lead.vars and lead.vars['firstName']):
                    warnings.append("Missing firstName variable")
            
            elif var == 'companyName':
                if not lead.company:
                    warnings.append("Missing company name")
            
            elif var == 'industry':
                if not (lead.vars and 'industry' in lead.vars and lead.vars['industry']):
                    warnings.append("Missing industry variable")
            
            elif var == 'email':
                if not lead.email:
                    warnings.append("Missing email address")
    
    return warnings


def render_preview(template_id: str, lead_id: str, store: LeadsStore) -> dict:
    """
    Enhanced template preview with comprehensive variable validation.
    - Extracts variables from template
    - Validates lead data against required variables
    - Provides detailed warnings for missing data
    - Renders preview with proper variable substitution
    """
    # Get lead
    lead = store.get(lead_id)
    if not lead:
        return {"html": "", "text": "", "warnings": ["Lead not found"]}

    # Get template (mock for now - in production would fetch from template_store)
    template = _get_mock_template(template_id)
    if not template:
        return {"html": "", "text": "", "warnings": ["Template not found"]}

    # Extract variables from template
    template_vars = extract_template_variables(template['bodyHtml'])
    subject_vars = extract_template_variables(template['subject'])
    all_vars = template_vars.union(subject_vars)

    # Validate variables against lead data
    warnings = validate_lead_variables(lead, all_vars)

    # Render template with variable substitution
    html = _substitute_variables(template['bodyHtml'], lead)
    subject = _substitute_variables(template['subject'], lead)
    
    # Create text version
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text).strip()

    return {
        "html": html,
        "text": text,
        "subject": subject,
        "warnings": warnings,
        "variables_found": list(all_vars),
        "variables_missing": [w.split(': ')[1] if ': ' in w else w for w in warnings]
    }


def _get_mock_template(template_id: str) -> Dict[str, Any]:
    """Mock template data - in production would use template_store"""
    templates = {
        "1": {
            "id": "1",
            "name": "Welcome Email",
            "subject": "Welcome to {{companyName}}, {{firstName}}!",
            "bodyHtml": """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #2563eb;">Hi {{firstName}},</h1>
                <p>Welcome to {{companyName}}! We're excited to have you on board.</p>
                <img src="{{image.cid 'hero'}}" alt="Welcome" style="width: 100%; max-width: 400px;" />
                <p>As a company in the {{industry}} sector, we believe you'll find great value in our services.</p>
                <p>Best regards,<br>The {{companyName}} Team</p>
            </div>
            """
        }
    }
    return templates.get(template_id)


def _substitute_variables(content: str, lead: Any) -> str:
    """Substitute template variables with lead data"""
    # Get lead data
    first_name = (lead.vars and lead.vars.get('firstName')) or lead.email.split('@')[0] if lead.email else 'Friend'
    company_name = lead.company or 'Your Company'
    industry = (lead.vars and lead.vars.get('industry')) or 'Business'
    
    # Perform substitutions
    content = content.replace('{{firstName}}', escape(first_name))
    content = content.replace('{{companyName}}', escape(company_name))
    content = content.replace('{{industry}}', escape(industry))
    content = content.replace('{{email}}', escape(lead.email or ''))
    
    # Handle image CID
    if lead.image_key:
        # In production, this would generate actual signed URL
        image_url = f"https://example.com/assets/{escape(lead.image_key)}.png"
        content = re.sub(r'\{\{image\.cid\s+[\'"][^\'"]*[\'"]\}\}', f'src="{image_url}"', content)
    else:
        # Placeholder for missing image
        placeholder_url = "https://via.placeholder.com/400x200?text=Missing+Image"
        content = re.sub(r'\{\{image\.cid\s+[\'"][^\'"]*[\'"]\}\}', f'src="{placeholder_url}"', content)
    
    return content
