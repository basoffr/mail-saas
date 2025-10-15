from dataclasses import dataclass
from typing import Dict, List, Optional
import re


@dataclass(frozen=True)
class HardCodedTemplate:
    """Hard-coded email template."""
    id: str
    version: int
    mail_number: int
    subject: str
    body: str
    placeholders: List[str]
    
    def render(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Render template with variables."""
        rendered_subject = self.subject
        rendered_body = self.body
        
        # Replace placeholders
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            rendered_subject = rendered_subject.replace(placeholder, str(value))
            rendered_body = rendered_body.replace(placeholder, str(value))
        
        return {
            "subject": rendered_subject,
            "body": rendered_body
        }
    
    def get_placeholders(self) -> List[str]:
        """Extract all placeholders from subject and body."""
        text = self.subject + " " + self.body
        # Extract {{variable}} and {{function 'param'}} patterns
        placeholders = re.findall(r'\{\{([^}\s]+)(?:\s+[^}]*)?\}\}', text)
        return list(set(placeholders))


# Hard-coded templates (v1-v4, mail 1-4 each = 16 total)
HARD_CODED_TEMPLATES = {
    # Version 1 (punthelder-marketing.nl)
    "v1_mail1": HardCodedTemplate(
        id="v1_mail1",
        version=1,
        mail_number=1,
        subject="Gratis SEO-analyse voor {{lead.company}}",
        body="""Hallo,

Ik ben Christian van Punthelder Marketing en help bedrijven zoals {{lead.company}} om beter gevonden te worden in Google.

Uw website {{lead.url}} heeft potentieel, maar er zijn waarschijnlijk nog kansen om hoger te scoren voor belangrijke zoektermen zoals "{{vars.keyword}}".

Momenteel staat u op positie {{vars.google_rank}} voor deze term. Met de juiste aanpassingen kunnen we dit flink verbeteren.

Ik bied u een gratis SEO-analyse aan waarin ik precies laat zien:
- Waar u nu staat ten opzichte van concurrenten
- Welke quick wins er mogelijk zijn
- Een concrete actieplan voor de komende maanden

{{image.cid 'dashboard'}}

Heeft u interesse in een korte kennismaking? Ik kan volgende week een analyse voor u maken.

Met vriendelijke groet,
Christian
Punthelder Marketing
christian@punthelder.nl
06-12345678""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v1_mail2": HardCodedTemplate(
        id="v1_mail2",
        version=1,
        mail_number=2,
        subject="Follow-up: SEO-kansen voor {{lead.company}}",
        body="""Hallo,

Een paar dagen geleden stuurde ik u een mail over SEO-mogelijkheden voor {{lead.company}}.

Ik begrijp dat u het druk heeft, maar wilde u nog even attenderen op de kansen die ik zie voor uw website {{lead.url}}.

Specifiek voor de zoekterm "{{vars.keyword}}" (waar u nu op positie {{vars.google_rank}} staat) zie ik concrete verbetermogelijkheden die relatief snel resultaat kunnen opleveren.

De gratis analyse die ik aanbied geeft u inzicht in:
✓ Uw huidige SEO-score
✓ Wat uw directe concurrenten anders doen  
✓ 3-5 concrete actiepunten voor snelle resultaten

{{image.cid 'dashboard'}}

Zal ik deze week een analyse voor u maken? Het kost u niets en u bent nergens toe verplicht.

Met vriendelijke groet,
Christian
Punthelder Marketing""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v1_mail3": HardCodedTemplate(
        id="v1_mail3",
        version=1,
        mail_number=3,
        subject="Laatste kans: gratis SEO-analyse {{lead.company}}",
        body="""Hallo,

Victor hier van Punthelder Marketing. Christian heeft me gevraagd om contact met u op te nemen over de SEO-analyse voor {{lead.company}}.

Ik zie dat u nog niet heeft gereageerd op zijn aanbod voor een gratis analyse van {{lead.url}}. Dat is jammer, want er liggen echt kansen voor u.

Voor "{{vars.keyword}}" staat u nu op positie {{vars.google_rank}}. Met een paar gerichte aanpassingen kunnen we dit flink verbeteren.

{{image.cid 'dashboard'}}

Dit is mijn laatste mail hierover. Als u interesse heeft, laat het me dan deze week weten.

Anders neem ik aan dat het nu niet het juiste moment is en hoor ik graag van u als dat verandert.

Met vriendelijke groet,
Victor
Punthelder Marketing
victor@punthelder.nl""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v1_mail4": HardCodedTemplate(
        id="v1_mail4",
        version=1,
        mail_number=4,
        subject="Afscheid van {{lead.company}} - Victor",
        body="""Hallo,

Victor hier. Dit is mijn laatste mail over de SEO-mogelijkheden voor {{lead.company}}.

Ik respecteer dat u op dit moment geen interesse heeft in een SEO-analyse voor {{lead.url}}.

Mocht u in de toekomst toch willen weten hoe u beter kunt scoren voor termen zoals "{{vars.keyword}}", dan kunt u altijd contact opnemen.

{{image.cid 'dashboard'}}

Ik wens u veel succes met uw bedrijf.

Met vriendelijke groet,
Victor
Punthelder Marketing""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "image.cid"]
    ),
    
    # Version 2 (punthelder-vindbaarheid.nl)
    "v2_mail1": HardCodedTemplate(
        id="v2_mail1",
        version=2,
        mail_number=1,
        subject="Vindbaarheid verbeteren voor {{lead.company}}?",
        body="""Hallo,

Christian van Punthelder Vindbaarheid. Ik help bedrijven zoals {{lead.company}} om beter vindbaar te worden online.

Uw website {{lead.url}} heeft potentieel, maar ik zie kansen om de vindbaarheid te verbeteren voor belangrijke zoektermen zoals "{{vars.keyword}}".

Momenteel staat u op positie {{vars.google_rank}} voor deze term. Er is ruimte voor verbetering.

Ik bied u een gratis vindbaarheidsanalyse aan:
- Huidige positie vs concurrenten
- Concrete verbeterpunten
- Stappenplan voor betere vindbaarheid

{{image.cid 'dashboard'}}

Interesse in een gratis analyse? Ik kan deze week voor u aan de slag.

Met vriendelijke groet,
Christian
Punthelder Vindbaarheid""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v2_mail2": HardCodedTemplate(
        id="v2_mail2",
        version=2,
        mail_number=2,
        subject="Nog steeds interesse in betere vindbaarheid?",
        body="""Hallo,

Christian hier van Punthelder Vindbaarheid. Ik stuurde u eerder een mail over vindbaarheid voor {{lead.company}}.

Voor {{lead.url}} zie ik nog steeds concrete kansen, vooral voor "{{vars.keyword}}" waar u nu op positie {{vars.google_rank}} staat.

De gratis analyse die ik aanbied laat precies zien:
✓ Waar u nu staat
✓ Wat er beter kan
✓ Hoe u meer bezoekers kunt krijgen

{{image.cid 'dashboard'}}

Zal ik deze week een analyse maken? Het is gratis en vrijblijvend.

Met vriendelijke groet,
Christian""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v2_mail3": HardCodedTemplate(
        id="v2_mail3",
        version=2,
        mail_number=3,
        subject="Victor hier - laatste kans vindbaarheidsanalyse",
        body="""Hallo,

Victor van Punthelder Vindbaarheid. Christian vroeg me contact met u op te nemen over {{lead.company}}.

U heeft nog niet gereageerd op het aanbod voor een gratis vindbaarheidsanalyse van {{lead.url}}.

Voor "{{vars.keyword}}" staat u op positie {{vars.google_rank}}. Dat kan echt beter.

{{image.cid 'dashboard'}}

Dit is mijn laatste mail hierover. Interesse? Laat het me deze week weten.

Met vriendelijke groet,
Victor""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v2_mail4": HardCodedTemplate(
        id="v2_mail4",
        version=2,
        mail_number=4,
        subject="Afscheid - Victor van Punthelder Vindbaarheid",
        body="""Hallo,

Victor hier. Laatste mail over vindbaarheid voor {{lead.company}}.

Ik begrijp dat u nu geen interesse heeft in verbetering van {{lead.url}}.

Mocht dat in de toekomst veranderen, vooral voor termen zoals "{{vars.keyword}}", dan hoor ik graag van u.

{{image.cid 'dashboard'}}

Succes gewenst!

Victor
Punthelder Vindbaarheid""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "image.cid"]
    ),
    
    # Version 3 (punthelder-seo.nl)
    "v3_mail1": HardCodedTemplate(
        id="v3_mail1",
        version=3,
        mail_number=1,
        subject="SEO-audit voor {{lead.company}} - gratis",
        body="""Hallo,

Christian van Punthelder SEO. Ik help bedrijven zoals {{lead.company}} met zoekmachine-optimalisatie.

Uw website {{lead.url}} kan waarschijnlijk beter presteren in Google, vooral voor zoektermen zoals "{{vars.keyword}}".

U staat nu op positie {{vars.google_rank}} voor deze term. Met de juiste SEO-aanpak kunnen we dit verbeteren.

Ik bied u een gratis SEO-audit aan:
- Technische SEO-analyse
- Content optimalisatie tips
- Linkbuilding mogelijkheden

{{image.cid 'dashboard'}}

Interesse? Ik kan deze week een audit voor u uitvoeren.

Met vriendelijke groet,
Christian
Punthelder SEO""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v3_mail2": HardCodedTemplate(
        id="v3_mail2",
        version=3,
        mail_number=2,
        subject="Follow-up SEO-audit {{lead.company}}",
        body="""Hallo,

Christian van Punthelder SEO. Ik stuurde u eerder een mail over een gratis SEO-audit voor {{lead.company}}.

Voor {{lead.url}} zie ik nog steeds SEO-kansen, vooral voor "{{vars.keyword}}" (positie {{vars.google_rank}}).

De gratis audit bevat:
✓ Technische SEO-check
✓ Content analyse
✓ Concurrentie vergelijking

{{image.cid 'dashboard'}}

Zal ik deze week een audit maken? Volledig gratis.

Met vriendelijke groet,
Christian""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v3_mail3": HardCodedTemplate(
        id="v3_mail3",
        version=3,
        mail_number=3,
        subject="Victor - laatste kans SEO-audit",
        body="""Hallo,

Victor van Punthelder SEO. Christian vroeg me u te benaderen over {{lead.company}}.

U heeft nog niet gereageerd op de gratis SEO-audit voor {{lead.url}}.

Voor "{{vars.keyword}}" staat u op positie {{vars.google_rank}}. Daar valt winst te behalen.

{{image.cid 'dashboard'}}

Laatste kans voor de gratis audit. Interesse? Laat het me weten.

Met vriendelijke groet,
Victor""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v3_mail4": HardCodedTemplate(
        id="v3_mail4",
        version=3,
        mail_number=4,
        subject="Afscheid SEO-audit - Victor",
        body="""Hallo,

Victor hier. Laatste mail over SEO voor {{lead.company}}.

Ik respecteer dat u geen interesse heeft in SEO-verbetering voor {{lead.url}}.

Mocht u later toch willen weten hoe u beter kunt scoren voor "{{vars.keyword}}", dan kunt u contact opnemen.

{{image.cid 'dashboard'}}

Veel succes!

Victor
Punthelder SEO""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "image.cid"]
    ),
    
    # Version 4 (punthelder-zoekmachine.nl) - kopie van v2
    "v4_mail1": HardCodedTemplate(
        id="v4_mail1",
        version=4,
        mail_number=1,
        subject="Zoekmachine optimalisatie voor {{lead.company}}",
        body="""Hallo,

Christian van Punthelder Zoekmachine. Ik help bedrijven zoals {{lead.company}} om beter gevonden te worden.

Uw website {{lead.url}} heeft potentieel, maar ik zie kansen voor zoekmachine optimalisatie, vooral voor "{{vars.keyword}}".

Momenteel staat u op positie {{vars.google_rank}} voor deze term. Er is ruimte voor verbetering.

Ik bied u een gratis zoekmachine-analyse aan:
- Huidige positie analyse
- Optimalisatie mogelijkheden  
- Concrete actieplan

{{image.cid 'dashboard'}}

Interesse in een gratis analyse? Ik kan deze week voor u aan de slag.

Met vriendelijke groet,
Christian
Punthelder Zoekmachine""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v4_mail2": HardCodedTemplate(
        id="v4_mail2",
        version=4,
        mail_number=2,
        subject="Follow-up zoekmachine optimalisatie",
        body="""Hallo,

Christian hier van Punthelder Zoekmachine. Ik stuurde u eerder een mail over optimalisatie voor {{lead.company}}.

Voor {{lead.url}} zie ik nog steeds concrete kansen, vooral voor "{{vars.keyword}}" waar u nu op positie {{vars.google_rank}} staat.

De gratis analyse laat zien:
✓ Waar u nu staat
✓ Wat er beter kan
✓ Hoe u meer bezoekers krijgt

{{image.cid 'dashboard'}}

Zal ik deze week een analyse maken? Het is gratis en vrijblijvend.

Met vriendelijke groet,
Christian""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v4_mail3": HardCodedTemplate(
        id="v4_mail3",
        version=4,
        mail_number=3,
        subject="Victor - laatste kans zoekmachine analyse",
        body="""Hallo,

Victor van Punthelder Zoekmachine. Christian vroeg me contact met u op te nemen over {{lead.company}}.

U heeft nog niet gereageerd op het aanbod voor een gratis zoekmachine-analyse van {{lead.url}}.

Voor "{{vars.keyword}}" staat u op positie {{vars.google_rank}}. Dat kan echt beter.

{{image.cid 'dashboard'}}

Dit is mijn laatste mail hierover. Interesse? Laat het me deze week weten.

Met vriendelijke groet,
Victor""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]
    ),
    
    "v4_mail4": HardCodedTemplate(
        id="v4_mail4",
        version=4,
        mail_number=4,
        subject="Afscheid - Victor van Punthelder Zoekmachine",
        body="""Hallo,

Victor hier. Laatste mail over zoekmachine optimalisatie voor {{lead.company}}.

Ik begrijp dat u nu geen interesse heeft in verbetering van {{lead.url}}.

Mocht dat in de toekomst veranderen, vooral voor termen zoals "{{vars.keyword}}", dan hoor ik graag van u.

{{image.cid 'dashboard'}}

Succes gewenst!

Victor
Punthelder Zoekmachine""",
        placeholders=["lead.company", "lead.url", "vars.keyword", "image.cid"]
    )
}


def get_template(template_id: str) -> Optional[HardCodedTemplate]:
    """Get template by ID."""
    return HARD_CODED_TEMPLATES.get(template_id)


def get_templates_for_version(version: int) -> List[HardCodedTemplate]:
    """Get all templates for a specific version."""
    return [
        template for template in HARD_CODED_TEMPLATES.values()
        if template.version == version
    ]


def get_all_templates() -> Dict[str, HardCodedTemplate]:
    """Get all templates."""
    return HARD_CODED_TEMPLATES.copy()


def get_template_for_flow(version: int, mail_number: int) -> Optional[HardCodedTemplate]:
    """Get specific template for version and mail number."""
    template_id = f"v{version}_mail{mail_number}"
    return get_template(template_id)


def validate_template_id(template_id: str) -> bool:
    """Validate if template ID exists."""
    return template_id in HARD_CODED_TEMPLATES


def get_templates_summary() -> List[Dict]:
    """Get summary of all templates for UI."""
    summaries = []
    
    for template in HARD_CODED_TEMPLATES.values():
        summaries.append({
            "id": template.id,
            "version": template.version,
            "mail_number": template.mail_number,
            "subject": template.subject,
            "placeholders": template.get_placeholders(),
            "body_preview": template.body[:100] + "..." if len(template.body) > 100 else template.body
        })
    
    return sorted(summaries, key=lambda x: (x["version"], x["mail_number"]))
