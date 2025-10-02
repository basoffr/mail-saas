"""
Lead Enrichment Service - Voegt computed metadata toe aan leads.

Dit service verrijkt lead responses met:
- has_report: boolean of er een rapport gekoppeld is
- has_image: boolean of er een afbeelding is
- vars_completeness: compleetheid score van variabelen
- is_complete: boolean of lead volledig is (vars + report + image)
"""

from typing import Dict, Any, Optional
from app.models.lead import Lead
from app.services.template_variables import template_variables_service
from app.services.reports_store import reports_store


def enrich_lead_with_metadata(lead: Lead, include_completeness: bool = True) -> Dict[str, Any]:
    """
    Verrijk een lead met computed metadata fields.
    
    Args:
        lead: Lead model instance
        include_completeness: Of compleetheid data toegevoegd moet worden
        
    Returns:
        Dict met alle lead data + enriched fields:
        {
            ... (alle lead fields)
            'has_report': bool,
            'has_image': bool,
            'vars_completeness': {...},  # optional
            'is_complete': bool
        }
    """
    # Converteer lead naar dict
    lead_dict = {
        'id': lead.id,
        'email': lead.email,
        'company': lead.company,
        'url': lead.url,
        'domain': lead.domain,
        'status': lead.status,
        'tags': lead.tags,
        'image_key': lead.image_key,
        'last_emailed_at': lead.last_emailed_at,
        'last_open_at': lead.last_open_at,
        'vars': lead.vars,
        'stopped': lead.stopped,
        'created_at': lead.created_at,
        'updated_at': lead.updated_at
    }
    
    # Add list_name if exists (voor backwards compatibility)
    if hasattr(lead, 'list_name'):
        lead_dict['list_name'] = lead.list_name
    
    # Computed fields
    has_report = reports_store.get_report_for_lead(lead.id) is not None
    has_image = lead.image_key is not None and lead.image_key != ''
    
    # Variabelen compleetheid (optioneel, kan performance impact hebben)
    vars_completeness = None
    is_complete = False
    
    if include_completeness:
        vars_completeness = template_variables_service.calculate_completeness(lead)
        is_complete = has_report and has_image and vars_completeness['is_complete']
    else:
        # Simplified completeness check without full calculation
        is_complete = has_report and has_image and bool(lead.vars)
    
    # Add enriched fields
    lead_dict['has_report'] = has_report
    lead_dict['has_image'] = has_image
    
    if vars_completeness:
        lead_dict['vars_completeness'] = vars_completeness
    
    lead_dict['is_complete'] = is_complete
    
    return lead_dict


def enrich_leads_bulk(leads: list[Lead], include_completeness: bool = False) -> list[Dict[str, Any]]:
    """
    Verrijk meerdere leads tegelijk (optimized voor list views).
    
    Args:
        leads: List van Lead instances
        include_completeness: Of full compleetheid berekend moet worden
                             (False voor performance in lijsten)
    
    Returns:
        List van enriched lead dicts
    """
    enriched_leads = []
    
    for lead in leads:
        enriched_lead = enrich_lead_with_metadata(lead, include_completeness=include_completeness)
        enriched_leads.append(enriched_lead)
    
    return enriched_leads


def get_lead_variables_detail(lead: Lead) -> Dict[str, Any]:
    """
    Haal gedetailleerde variabelen info op voor een lead (voor drawer view).
    
    Returns:
        {
            'all_variables': ['lead.company', 'lead.url', ...],
            'filled_variables': ['lead.company', 'vars.keyword'],
            'missing_variables': ['vars.google_rank', 'image.cid'],
            'variable_values': {
                'lead.company': 'Acme Inc',
                'vars.keyword': 'SEO',
                ...
            },
            'completeness': {...}
        }
    """
    all_vars = sorted(template_variables_service.get_all_required_variables())
    missing_vars = template_variables_service.get_missing_variables(lead)
    filled_vars = [v for v in all_vars if v not in missing_vars and not v.startswith('campaign.')]
    
    # Get actual values
    variable_values = {}
    for var in filled_vars:
        value = template_variables_service.get_variable_value(lead, var)
        if value:
            variable_values[var] = value
    
    completeness = template_variables_service.calculate_completeness(lead)
    
    return {
        'all_variables': all_vars,
        'filled_variables': filled_vars,
        'missing_variables': missing_vars,
        'variable_values': variable_values,
        'completeness': completeness
    }


def check_lead_is_complete(lead: Lead) -> bool:
    """
    Quick check of lead is volledig (voor filtering).
    
    Args:
        lead: Lead instance
        
    Returns:
        True als lead alle vars, report EN image heeft
    """
    has_report = reports_store.get_report_for_lead(lead.id) is not None
    has_image = lead.image_key is not None and lead.image_key != ''
    vars_complete = len(template_variables_service.get_missing_variables(lead)) == 0
    
    return has_report and has_image and vars_complete
