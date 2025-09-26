from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models.template import Template
from app.schemas.template import TemplateVarItem


class TemplateStore:
    """In-memory template store for MVP"""
    
    def __init__(self):
        self.templates = self._create_seed_templates()
    
    def _create_seed_templates(self) -> Dict[str, Template]:
        """Create seed templates for MVP"""
        templates = {}
        
        # Template 1: Welcome Email
        welcome_template = Template(
            id="welcome-001",
            name="Welcome Email",
            subject_template="Welkom {{lead.company | default 'daar'}}! 🎉",
            body_template="""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                    {{image.url 'logo'}}
                    <h1 style="color: white; margin: 20px 0;">Welkom bij onze service!</h1>
                </div>
                
                <div style="padding: 30px;">
                    <p>Hallo {{lead.email}},</p>
                    
                    <p>Bedankt voor je interesse in onze service! We zijn blij je te verwelkomen.</p>
                    
                    {{#if lead.company}}
                    <p>We zien dat je werkt bij <strong>{{lead.company}}</strong>. Geweldig!</p>
                    {{/if}}
                    
                    {{#if vars.industry}}
                    <p>Als bedrijf in de <strong>{{vars.industry}}</strong> sector, denken we dat onze oplossing perfect bij je past.</p>
                    {{/if}}
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>Wat kun je verwachten?</h3>
                        <ul>
                            <li>Persoonlijke begeleiding</li>
                            <li>24/7 ondersteuning</li>
                            <li>Gratis onboarding</li>
                        </ul>
                    </div>
                    
                    {{image.cid 'hero'}}
                    
                    <p>Heb je vragen? Reageer gewoon op deze email!</p>
                    
                    <p>Met vriendelijke groet,<br>
                    Het {{campaign.name | default 'Team'}} Team</p>
                </div>
                
                <div style="background: #f1f3f4; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                    <p>Je ontvangt deze email omdat je interesse hebt getoond in onze service.</p>
                    <p><a href="{{unsubscribe_url}}">Uitschrijven</a></p>
                </div>
            </body>
            </html>
            """,
            updated_at=datetime(2025, 9, 20, 10, 0, 0),
            required_vars=["lead.email", "lead.company", "vars.industry"],
            assets=[
                {"key": "logo", "type": "static"},
                {"key": "hero", "type": "cid"}
            ]
        )
        templates[welcome_template.id] = welcome_template
        
        # Template 2: Follow-up Email
        followup_template = Template(
            id="followup-001",
            name="Follow-up Email",
            subject_template="{{lead.company | uppercase}} - Nog vragen over onze oplossing?",
            body_template="""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="padding: 30px;">
                    <h2>Hallo {{lead.email | default 'daar'}},</h2>
                    
                    <p>Een paar dagen geleden hebben we je gecontacteerd over onze service.</p>
                    
                    {{#if lead.company}}
                    <p>We begrijpen dat je als <strong>{{lead.company}}</strong> waarschijnlijk veel op je bordje hebt.</p>
                    {{/if}}
                    
                    <p>Daarom wilden we je nog even herinneren aan de voordelen:</p>
                    
                    <div style="background: #e3f2fd; padding: 20px; border-left: 4px solid #2196f3; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Waarom kiezen voor ons?</h3>
                        <ul>
                            <li><strong>Tijdsbesparing:</strong> Tot 80% minder handmatig werk</li>
                            <li><strong>Kosteneffectief:</strong> ROI binnen 3 maanden</li>
                            <li><strong>Betrouwbaar:</strong> 99.9% uptime garantie</li>
                        </ul>
                    </div>
                    
                    {{#if vars.company_size}}
                    <p>Voor een bedrijf van {{vars.company_size}} medewerkers schatten we een besparing van <strong>€{{vars.estimated_savings | default '5000'}}</strong> per maand.</p>
                    {{/if}}
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://calendly.com/demo" style="background: #4caf50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Plan een gratis demo
                        </a>
                    </div>
                    
                    <p>Heb je specifieke vragen? Reageer gewoon op deze email!</p>
                    
                    <p>Met vriendelijke groet,<br>
                    {{campaign.sender_name | default 'Het Team'}}</p>
                </div>
                
                <div style="background: #f1f3f4; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                    <p><a href="{{unsubscribe_url}}">Uitschrijven</a> | <a href="{{company_url}}">Website</a></p>
                </div>
            </body>
            </html>
            """,
            updated_at=datetime(2025, 9, 22, 14, 30, 0),
            required_vars=["lead.email", "lead.company", "vars.company_size"],
            assets=[]
        )
        templates[followup_template.id] = followup_template
        
        return templates
    
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
