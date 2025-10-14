"""
Central Store Factory - Automatically selects DB or in-memory stores
Based on USE_IN_MEMORY_STORES environment variable
"""
import os
import logging

logger = logging.getLogger(__name__)

# Determine if we should use database stores
USE_DB = os.getenv('USE_IN_MEMORY_STORES', 'true').lower() == 'false'

logger.info(f"Store Factory: USE_DB={USE_DB}, USE_IN_MEMORY_STORES={os.getenv('USE_IN_MEMORY_STORES')}")

# ============================================================================
# LEADS STORE
# ============================================================================
try:
    if USE_DB:
        try:
            from app.services.db_leads_store import DBLeadsStore
            leads_store = DBLeadsStore()
            logger.info("✅ Using DBLeadsStore (Supabase database)")
        except Exception as e:
            logger.error(f"Failed to initialize DBLeadsStore: {e}, falling back to in-memory")
            from app.services.leads_store import LeadsStore
            leads_store = LeadsStore()
    else:
        from app.services.leads_store import LeadsStore
        leads_store = LeadsStore()
        logger.warning("⚠️  Using in-memory LeadsStore (development mode)")
except Exception as e:
    logger.critical(f"CRITICAL: Failed to initialize any leads store: {e}")
    from app.services.leads_store import LeadsStore
    leads_store = LeadsStore()
    logger.warning("Emergency fallback: using in-memory LeadsStore")

# ============================================================================
# TEMPLATES STORE
# ============================================================================
try:
    if USE_DB:
        try:
            from app.services.db_template_store import DBTemplateStore
            templates_store = DBTemplateStore()
            logger.info("✅ Using DBTemplateStore (Supabase database)")
        except Exception as e:
            logger.error(f"Failed to initialize DBTemplateStore: {e}, falling back to in-memory")
            from app.services.template_store import TemplateStore
            templates_store = TemplateStore()
    else:
        from app.services.template_store import TemplateStore
        templates_store = TemplateStore()
        logger.warning("⚠️  Using in-memory TemplateStore (development mode)")
except Exception as e:
    logger.critical(f"CRITICAL: Failed to initialize any templates store: {e}")
    from app.services.template_store import TemplateStore
    templates_store = TemplateStore()
    logger.warning("Emergency fallback: using in-memory TemplateStore")

# ============================================================================
# CAMPAIGNS STORE
# ============================================================================
try:
    if USE_DB:
        try:
            from app.services.db_campaign_store import DBCampaignStore
            campaigns_store = DBCampaignStore()
            logger.info("✅ Using DBCampaignStore (Supabase database)")
        except Exception as e:
            logger.error(f"Failed to initialize DBCampaignStore: {e}, falling back to in-memory")
            from app.services.campaign_store import CampaignStore
            campaigns_store = CampaignStore()
    else:
        from app.services.campaign_store import CampaignStore
        campaigns_store = CampaignStore()
        logger.warning("⚠️  Using in-memory CampaignStore (development mode)")
except Exception as e:
    logger.critical(f"CRITICAL: Failed to initialize campaigns store: {e}")
    # Create minimal fallback
    campaigns_store = None

# ============================================================================
# REPORTS STORE - Direct Storage Access (No Database)
# ============================================================================
try:
    from app.services.storage_reports_store import StorageReportsStore
    reports_store = StorageReportsStore()
    logger.info("✅ Using StorageReportsStore (Direct Supabase Storage access - no DB)")
except Exception as e:
    logger.error(f"Failed to initialize StorageReportsStore: {e}, falling back to in-memory")
    from app.services.reports_store import ReportsStore
    reports_store = ReportsStore()
    logger.warning("⚠️ Using in-memory ReportsStore (fallback)")

# ============================================================================
# EXPORT SUMMARY
# ============================================================================
def get_stores_summary():
    """Get summary of which stores are being used"""
    # Check store types safely
    leads_type = "unknown"
    try:
        if hasattr(leads_store, '__class__'):
            leads_type = "database" if "DB" in leads_store.__class__.__name__ else "in-memory"
    except:
        leads_type = "unknown"
    
    templates_type = "unknown"
    try:
        if hasattr(templates_store, '__class__'):
            templates_type = "database" if "DB" in templates_store.__class__.__name__ else "in-memory"
    except:
        templates_type = "unknown"
    
    campaigns_type = "unknown"
    try:
        if hasattr(campaigns_store, '__class__'):
            campaigns_type = "database" if "DB" in campaigns_store.__class__.__name__ else "in-memory"
    except:
        campaigns_type = "unknown"
    
    reports_type = "unknown"
    try:
        if hasattr(reports_store, '__class__'):
            reports_type = "database" if "DB" in reports_store.__class__.__name__ else "in-memory"
    except:
        reports_type = "unknown"
    
    return {
        "use_database": USE_DB,
        "stores": {
            "leads": leads_type,
            "templates": templates_type,
            "campaigns": campaigns_type,
            "reports": reports_type,
        }
    }

# Log startup summary
logger.info(f"Store Factory Summary: {get_stores_summary()}")
