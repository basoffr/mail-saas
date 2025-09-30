import re
from typing import Dict, Any, List, Optional
from datetime import datetime


class TemplateRenderer:
    """Template rendering engine with variable interpolation"""
    
    def __init__(self):
        self.variable_pattern = re.compile(r'\{\{\s*([^}]+)\s*\}\}')
    
    def render(self, template: str, context: Dict[str, Any]) -> tuple[str, List[str]]:
        """Render template with context, return (rendered_text, warnings)"""
        warnings = []
        rendered = template
        
        # Find all variables in template
        variables = self.variable_pattern.findall(template)
        
        for var in variables:
            var = var.strip()
            placeholder = f"{{{{{var}}}}}"
            
            try:
                # Handle different variable types
                if var.startswith('lead.'):
                    value = self._get_lead_value(var, context.get('lead', {}), warnings)
                elif var.startswith('vars.'):
                    value = self._get_vars_value(var, context.get('vars', {}), warnings)
                elif var.startswith('campaign.'):
                    value = self._get_campaign_value(var, context.get('campaign', {}), warnings)
                elif var.startswith('image.'):
                    value = self._get_image_value(var, context, warnings)
                elif '|' in var:  # Helper functions
                    value = self._apply_helper(var, context, warnings)
                else:
                    value = context.get(var, '')
                    if not value:
                        warnings.append(f"Variable '{var}' not found")
                
                rendered = rendered.replace(placeholder, str(value) if value is not None else '')
                
            except Exception as e:
                warnings.append(f"Error processing variable '{var}': {str(e)}")
                rendered = rendered.replace(placeholder, '')
        
        return rendered, warnings
    
    def _get_lead_value(self, var: str, lead: Dict[str, Any], warnings: List[str]) -> str:
        """Get value from lead context"""
        field = var.replace('lead.', '')
        value = lead.get(field, '')
        if not value and field in ['email', 'company']:
            warnings.append(f"Required lead field '{field}' is missing")
        return str(value) if value else ''
    
    def _get_vars_value(self, var: str, vars_dict: Dict[str, Any], warnings: List[str]) -> str:
        """Get value from vars context"""
        field = var.replace('vars.', '')
        value = vars_dict.get(field, '')
        if not value:
            warnings.append(f"Variable 'vars.{field}' not found in lead data")
        return str(value) if value else ''
    
    def _get_campaign_value(self, var: str, campaign: Dict[str, Any], warnings: List[str]) -> str:
        """Get value from campaign context"""
        field = var.replace('campaign.', '')
        value = campaign.get(field, '')
        if not value:
            warnings.append(f"Campaign variable '{field}' not available")
        return str(value) if value else ''
    
    def _get_image_value(self, var: str, context: Dict[str, Any], warnings: List[str]) -> str:
        """Handle image variables"""
        if 'image.cid' in var:
            # Extract slot name: image.cid 'hero' -> hero or 'dashboard' -> dashboard
            slot_match = re.search(r"image\.cid\s+['\"]([^'\"]+)['\"]", var)
            if slot_match:
                slot = slot_match.group(1)
                
                # Special handling for dashboard images (implementation plan)
                if slot == 'dashboard':
                    domain = context.get('domain', '')
                    if domain:
                        # Lazy import to avoid circular imports
                        from app.services.asset_resolver import asset_resolver
                        if asset_resolver.has_dashboard_image(domain):
                            return f"cid:dashboard_{domain.replace('.', '_')}"
                        else:
                            warnings.append(f"Dashboard image not found for domain: {domain}")
                            return ""  # Return empty as per plan (permissive)
                    else:
                        warnings.append("No domain provided for dashboard image")
                        return ""
                
                # Regular per-lead images
                lead = context.get('lead', {})
                image_key = lead.get('image_key', '')
                if not image_key:
                    warnings.append(f"No image available for slot '{slot}'")
                    return f"[IMAGE_PLACEHOLDER_{slot.upper()}]"
                return f"cid:{image_key}_{slot}"
            else:
                warnings.append(f"Invalid image.cid syntax: {var}")
                return "[IMAGE_ERROR]"
        
        elif 'image.url' in var:
            # Extract asset key: image.url 'logo' -> logo
            key_match = re.search(r"image\.url\s+['\"]([^'\"]+)['\"]", var)
            if key_match:
                key = key_match.group(1)
                return f"https://assets.example.com/{key}.png"
            else:
                warnings.append(f"Invalid image.url syntax: {var}")
                return "[IMAGE_ERROR]"
        
        return "[IMAGE_ERROR]"
    
    def _apply_helper(self, var: str, context: Dict[str, Any], warnings: List[str]) -> str:
        """Apply helper functions like default, uppercase, etc."""
        if '|' not in var:
            return ''
        
        parts = [p.strip() for p in var.split('|')]
        value = parts[0]
        helpers = parts[1:]
        
        # Get initial value
        if value.startswith('lead.'):
            result = self._get_lead_value(value, context.get('lead', {}), warnings)
        elif value.startswith('vars.'):
            result = self._get_vars_value(value, context.get('vars', {}), warnings)
        else:
            result = context.get(value, '')
        
        # Apply helpers
        for helper in helpers:
            if helper.startswith('default'):
                # Extract default value: default 'fallback'
                default_match = re.search(r"default\s+['\"]([^'\"]+)['\"]", helper)
                if default_match and not result:
                    result = default_match.group(1)
            elif helper == 'uppercase':
                result = str(result).upper()
            elif helper == 'lowercase':
                result = str(result).lower()
        
        return str(result)
    
    def extract_variables(self, template: str) -> List[str]:
        """Extract all variables from template"""
        return self.variable_pattern.findall(template)
    
    def validate_subject(self, subject: str) -> List[str]:
        """Validate rendered subject"""
        warnings = []
        if not subject.strip():
            warnings.append("Subject is empty after rendering")
        if len(subject) > 255:
            warnings.append(f"Subject too long ({len(subject)} chars, max 255)")
        return warnings


def inject_tracking_pixel(html: str, pixel_url: str) -> str:
    """
    Inject 1x1 tracking pixel before closing </body> tag.
    If no </body> tag found, append to end of HTML.
    """
    pixel_html = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none;" />'
    
    if '</body>' in html.lower():
        # Case-insensitive replacement
        import re
        return re.sub(r'</body>', f'{pixel_html}</body>', html, count=1, flags=re.IGNORECASE)
    else:
        # No body tag, append to end
        return html + pixel_html


def render_template_with_lead(template_body: str, subject_template: str, lead_data: Dict[str, Any], campaign_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Render template with lead data"""
    renderer = TemplateRenderer()
    
    # Prepare context
    context = {
        'lead': lead_data,
        'vars': lead_data.get('vars', {}),
        'campaign': campaign_data or {'name': 'Test Campaign', 'id': 'test'}
    }
    
    # Render subject and body
    rendered_subject, subject_warnings = renderer.render(subject_template, context)
    rendered_body, body_warnings = renderer.render(template_body, context)
    
    # Validate subject
    subject_validation_warnings = renderer.validate_subject(rendered_subject)
    
    # Generate plain text version (simple HTML strip)
    text_body = re.sub(r'<[^>]+>', '', rendered_body)
    text_body = re.sub(r'\s+', ' ', text_body).strip()
    
    # Combine all warnings
    all_warnings = subject_warnings + body_warnings + subject_validation_warnings
    
    return {
        'html': rendered_body,
        'text': text_body,
        'subject': rendered_subject,
        'warnings': all_warnings if all_warnings else None
    }
