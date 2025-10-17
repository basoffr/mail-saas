from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models.template import Template
from app.schemas.template import TemplateVarItem


class TemplateStore:
    """In-memory template store for MVP with hard-coded templates"""
    
    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self._init_hardcoded_templates()
    
    def _init_hardcoded_templates(self):
        """Initialize hard-coded templates for all 4 versions (v1-v4) with 4 mails each."""
        
        # Version 1 Templates (punthelder-marketing.nl)
        self.templates["v1m1"] = Template(
            id="v1m1",
            name="V1 Mail 1: Eerste kennismaking",
            subject_template="Gratis SEO-analyse voor {{lead.company}}",
            body_template="""Hallo,

Ik ben Christian van Punthelder Marketing en help bedrijven zoals {{lead.company}} om beter gevonden te worden in Google.

Uw website {{lead.url}} heeft potentieel, maar er zijn waarschijnlijk nog kansen om hoger te scoren voor belangrijke zoektermen zoals "{{vars.keyword}}".

Momenteel staat u op positie {{vars.google_rank}} voor deze term. Met de juiste aanpassingen kunnen we dit flink verbeteren.

Ik bied u een gratis SEO-analyse aan waarin ik precies laat zien:
- Waar u nu staat ten opzichte van concurrenten
- Welke quick wins er mogelijk zijn
- Een concrete actieplan voor de komende maanden

Heeft u interesse in een korte kennismaking? Ik kan volgende week een analyse voor u maken.

Met vriendelijke groet,
Christian
Punthelder Marketing
christian@punthelder-marketing.nl
06-12345678""",
            required_vars=["lead.company", "lead.url", "vars.keyword", "vars.google_rank"],
            updated_at=datetime.utcnow()
        )
        
        self.templates["v1m2"] = Template(
            id="v1m2",
            name="V1 Mail 2: Follow-up",
            subject_template="Follow-up: SEO-kansen voor {{lead.company}}",
            body_template="""Hallo,

Een paar dagen geleden stuurde ik u een mail over SEO-mogelijkheden voor {{lead.company}}.

Ik begrijp dat u het druk heeft, maar wilde u nog even attenderen op de kansen die ik zie voor uw website {{lead.url}}.

Specifiek voor de zoekterm "{{vars.keyword}}" (waar u nu op positie {{vars.google_rank}} staat) zie ik concrete verbetermogelijkheden die relatief snel resultaat kunnen opleveren.

De gratis analyse die ik aanbied geeft u inzicht in:
✓ Uw huidige SEO-score
✓ Wat uw directe concurrenten anders doen  
✓ 3-5 concrete actiepunten voor snelle resultaten

Zal ik deze week een analyse voor u maken? Het kost u niets en u bent nergens toe verplicht.

Met vriendelijke groet,
Christian
Punthelder Marketing""",
            required_vars=["lead.company", "lead.url", "vars.keyword", "vars.google_rank"],
            updated_at=datetime.utcnow()
        )
        
        self.templates["v1m3"] = Template(
            id="v1m3",
            name="V1 Mail 3: Victor neemt over",
            subject_template="Laatste kans: gratis SEO-analyse {{lead.company}}",
            body_template="""Hallo,

Victor hier van Punthelder Marketing. Christian heeft me gevraagd om contact met u op te nemen over de SEO-analyse voor {{lead.company}}.

Ik zie dat u nog niet heeft gereageerd op zijn aanbod voor een gratis analyse van {{lead.url}}. Dat is jammer, want er liggen echt kansen voor u.

Voor "{{vars.keyword}}" staat u nu op positie {{vars.google_rank}}. Met een paar gerichte aanpassingen kunnen we dit flink verbeteren.

Dit is mijn laatste mail hierover. Als u interesse heeft, laat het me dan deze week weten.

Anders neem ik aan dat het nu niet het juiste moment is en hoor ik graag van u als dat verandert.

Met vriendelijke groet,
Victor
Punthelder Marketing
victor@punthelder-marketing.nl""",
            required_vars=["lead.company", "lead.url", "vars.keyword", "vars.google_rank"],
            updated_at=datetime.utcnow()
        )
        
        self.templates["v1m4"] = Template(
            id="v1m4",
            name="V1 Mail 4: Afscheid",
            subject_template="Afscheid van {{lead.company}} - Victor",
            body_template="""Hallo,

Victor hier. Dit is mijn laatste mail over de SEO-mogelijkheden voor {{lead.company}}.

Ik respecteer dat u op dit moment geen interesse heeft in een SEO-analyse voor {{lead.url}}.

Mocht u in de toekomst toch willen weten hoe u beter kunt scoren voor termen zoals "{{vars.keyword}}", dan kunt u altijd contact opnemen.

Ik wens u veel succes met uw bedrijf.

Met vriendelijke groet,
Victor
Punthelder Marketing""",
            required_vars=["lead.company", "lead.url", "vars.keyword"],
            updated_at=datetime.utcnow()
        )
        
        # Version 2-4: Similar structure (shortened for brevity)
        # Add remaining 12 templates (v2m1-v2m4, v3m1-v3m4, v4m1-v4m4)
        # For now, using v1 templates as placeholders
        for version in [2, 3, 4]:
            for mail_num in [1, 2, 3, 4]:
                template_id = f"v{version}m{mail_num}"
                # Copy from v1 templates but with adjusted domain names
                domain_map = {
                    2: "punthelder-vindbaarheid.nl",
                    3: "punthelder-seo.nl", 
                    4: "punthelder-zoekmachine.nl"
                }
                
                # Get base template from v1
                base_template = self.templates[f"v1m{mail_num}"]
                
                # Create version-specific template
                self.templates[template_id] = Template(
                    id=template_id,
                    name=base_template.name.replace("V1", f"V{version}"),
                    subject_template=base_template.subject_template,
                    body_template=base_template.body_template.replace(
                        "Punthelder Marketing",
                        f"Punthelder {domain_map[version].split('-')[1].split('.')[0].capitalize()}"
                    ),
                    required_vars=base_template.required_vars,
                    updated_at=datetime.utcnow()
                )
    
    
    def get_all(self) -> List[Template]:
        """Get all templates"""
        return list(self.templates.values())
    
    def get_by_id(self, template_id: str) -> Optional[Template]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def get(self, template_id: str) -> Optional[Template]:
        """Alias for get_by_id for backwards compatibility."""
        return self.get_by_id(template_id)
    
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
