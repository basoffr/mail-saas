# 🏗️ FASE 3: HYBRID TEMPLATE STORE IMPLEMENTATIEPLAN

**Doel**: Templates migreren naar Database met fallback naar hard-coded templates  
**Strategie**: Database-first, hard-coded fallback (zero downtime)  
**Tijd**: 2-3 uur implementatie + 30 min testing  
**Datum**: 9 oktober 2025

---

## 🎯 **WAAROM HYBRID STORE?**

### **Huidige Situatie**
```
❌ Templates hard-coded in Python → Niet editeerbaar
❌ USE_IN_MEMORY_STORES beïnvloedt alle stores → Conflict
❌ Template changes vereisen code deployment → Traag
```

### **Na Hybrid Store**
```
✅ Templates in Database → Editeerbaar via UI
✅ Hard-coded fallback → Zero downtime bij DB issues
✅ Onafhankelijk van andere stores → Geen conflict
✅ Template changes zonder deployment → Snel
```

---

## 📊 **ARCHITECTUUR OVERZICHT**

### **Hybrid Template Store Flow**
```
Frontend Request (v1m1)
    ↓
Normalize ID (v1m1 → v1_mail1)
    ↓
Hybrid Store:
    1. Try Database (templates table)
    2. If not found → Fallback to Hard-coded
    3. If hard-coded not found → 404
    ↓
Return Template
```

### **Store Hiërarchie**
```
Priority 1: Database Templates (Supabase)
    ↓ (if None)
Priority 2: Hard-coded Templates (Python)
    ↓ (if None)
404 Not Found
```

---

## 🔧 **BENODIGDE COMPONENTEN**

### **1. Database Schema** (Reeds aanwezig! ✅)
```sql
-- Table: templates
CREATE TABLE templates (
    id TEXT PRIMARY KEY,                    -- v1_mail1, v2_mail3, etc.
    name TEXT NOT NULL,                     -- "V1 Mail 1: Eerste kennismaking"
    version INTEGER NOT NULL,               -- 1, 2, 3, 4
    mail_number INTEGER NOT NULL,           -- 1, 2, 3, 4
    subject_template TEXT NOT NULL,         -- "Gratis SEO-analyse voor {{lead.company}}"
    body_template TEXT NOT NULL,            -- HTML body met placeholders
    required_vars TEXT[] DEFAULT '{}',      -- ['lead.company', 'vars.keyword']
    assets JSONB DEFAULT '{}',              -- {"dashboard": true}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### **2. Database Seed Script** (NIEUW)
**Bestand**: `backend/scripts/seed_templates.sql`
- Bevat alle 16 templates (v1-v4, mail 1-4)
- INSERT statements met ON CONFLICT DO UPDATE
- Idempotent - kan meerdere keren gerund worden

### **3. Hybrid Template Service** (NIEUW)
**Bestand**: `backend/app/services/hybrid_template_service.py`
- `get_template(template_id)` → Try DB first, fallback hard-coded
- `get_all_templates()` → Merge DB + hard-coded templates
- `get_templates_by_version(version)` → Filter by version
- Caching layer voor performance

### **4. Update Templates API** (UPDATE)
**Bestand**: `backend/app/api/templates.py`
- Verwijder `USE_IN_MEMORY_STORES` checks
- Gebruik alleen `hybrid_template_service`
- Simplified code - 1 data source (hybrid)

### **5. Migration Script** (NIEUW)
**Bestand**: `backend/scripts/migrate_templates.py`
- Python script om seed SQL uit te voeren
- Connection naar Supabase via environment variables
- Verification na migratie

---

## 📝 **IMPLEMENTATIE STAPPEN**

### **STAP 1: Database Seed Script** (30 min)

**Actie**: Maak `backend/scripts/seed_templates.sql`

**Inhoud**: Alle 16 templates
```sql
-- Version 1 Templates (punthelder-marketing.nl)
INSERT INTO templates (
    id, name, version, mail_number,
    subject_template, body_template,
    required_vars, assets, updated_at
) VALUES
('v1_mail1', 'V1 Mail 1: Eerste kennismaking', 1, 1,
 'Gratis SEO-analyse voor {{lead.company}}',
 '<p>Hallo,</p><p>Ik ben Christian van Punthelder Marketing...</p>',
 ARRAY['lead.company', 'lead.url', 'vars.keyword', 'vars.google_rank'],
 '{"dashboard": true}'::jsonb,
 NOW()),

('v1_mail2', 'V1 Mail 2: Follow-up', 1, 2,
 'Follow-up: SEO-kansen voor {{lead.company}}',
 '<p>Hallo,</p><p>Een paar dagen geleden...</p>',
 ARRAY['lead.company', 'lead.url', 'vars.keyword', 'vars.google_rank'],
 '{"dashboard": true}'::jsonb,
 NOW()),

-- ... (alle 16 templates)

ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    subject_template = EXCLUDED.subject_template,
    body_template = EXCLUDED.body_template,
    required_vars = EXCLUDED.required_vars,
    assets = EXCLUDED.assets,
    updated_at = NOW();
```

**Verificatie**:
```sql
SELECT id, name, version, mail_number FROM templates ORDER BY version, mail_number;
-- Verwacht: 16 rows
```

---

### **STAP 2: Hybrid Template Service** (45 min)

**Actie**: Maak `backend/app/services/hybrid_template_service.py`

**Class Structure**:
```python
class HybridTemplateService:
    """
    Hybrid Template Service: Database-first with hard-coded fallback.
    
    Provides seamless access to templates from both database and
    hard-coded sources, with automatic fallback mechanism.
    """
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self._cache = {}  # Optional: in-memory cache
        
    def get_template(self, template_id: str) -> Optional[Template]:
        """
        Get template by ID (normalized).
        
        Flow:
        1. Try database
        2. If not found, try hard-coded
        3. If still not found, return None
        
        Args:
            template_id: Normalized template ID (v1_mail1)
            
        Returns:
            Template object or None
        """
        
    def get_all_templates(self) -> List[Template]:
        """
        Get all templates (merged from DB + hard-coded).
        Database templates override hard-coded ones.
        """
        
    def get_templates_by_version(self, version: int) -> List[Template]:
        """Get all templates for specific version (1-4)."""
        
    def refresh_cache(self):
        """Clear cache to force fresh data."""
```

**Key Features**:
- Database query via Supabase client
- Fallback to `app.core.templates_store.HARD_CODED_TEMPLATES`
- Template object normalization (DB format → Python object)
- Error handling (DB connection failures)
- Logging per decision (DB hit, fallback, cache)

---

### **STAP 3: Update Templates API** (30 min)

**Actie**: Refactor `backend/app/api/templates.py`

**Voor (Huidig)**:
```python
use_in_memory = os.getenv("USE_IN_MEMORY_STORES", "true").lower() == "true"

if use_in_memory:
    template = get_template(normalized_id)  # Hard-coded
else:
    template = templates_store.get_by_id(normalized_id)  # Database
```

**Na (Hybrid)**:
```python
from app.services.hybrid_template_service import hybrid_template_service

# Altijd hybrid - geen if/else!
template = hybrid_template_service.get_template(normalized_id)
```

**Te updaten endpoints**:
1. `GET /templates` - List all
2. `GET /templates/{id}` - Detail
3. `GET /templates/{id}/preview` - Preview
4. `GET /templates/{id}/variables` - Variables
5. `POST /templates/{id}/testsend` - Test send

**Code reductie**: ~40% minder code (geen if/else logic)

---

### **STAP 4: Migration Script** (20 min)

**Actie**: Maak `backend/scripts/migrate_templates.py`

```python
"""
Template Migration Script
Migrates hard-coded templates to Supabase database.
"""
import os
from supabase import create_client, Client
from pathlib import Path

def migrate_templates():
    """Run template migration."""
    
    # 1. Connect to Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # 2. Read seed SQL
    sql_path = Path(__file__).parent / "seed_templates.sql"
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 3. Execute SQL (via RPC or direct query)
    print("🚀 Starting template migration...")
    # Note: Supabase Python client doesn't support raw SQL
    # Alternative: Use psycopg2 or run manually in Supabase SQL editor
    
    # 4. Verify
    result = supabase.table('templates').select('id, name').execute()
    print(f"✅ Migration complete: {len(result.data)} templates in database")
    
    for template in result.data:
        print(f"   - {template['id']}: {template['name']}")

if __name__ == "__main__":
    migrate_templates()
```

**Uitvoeren**:
```bash
cd backend
python scripts/migrate_templates.py
```

**Alternatief** (SQL Editor):
1. Ga naar Supabase Dashboard → SQL Editor
2. Kopieer `seed_templates.sql` inhoud
3. Run query
4. Verify: `SELECT COUNT(*) FROM templates;` → Should be 16

---

### **STAP 5: Testing** (30 min)

**Unit Tests**: `backend/tests/services/test_hybrid_template_service.py`
```python
def test_get_template_from_database():
    """Test template retrieval from database."""
    
def test_get_template_fallback_to_hardcoded():
    """Test fallback when template not in database."""
    
def test_get_all_templates_merged():
    """Test merging of DB + hard-coded templates."""
    
def test_database_connection_failure_fallback():
    """Test graceful fallback on DB connection error."""
```

**Integration Tests**: Manual testing
1. Database template exists → Returns DB version
2. Database template missing → Returns hard-coded version
3. Both missing → Returns 404
4. Database down → Falls back to hard-coded (no 500 error)

**Frontend Tests**:
1. Open template detail → Shows DB content
2. Edit template in Supabase → Refresh → Shows updated content
3. Delete template from DB → Falls back to hard-coded version

---

### **STAP 6: Deployment** (15 min)

**Local Testing**:
```bash
# 1. Run migration
cd backend
python scripts/migrate_templates.py

# 2. Start backend
uvicorn app.main:app --reload

# 3. Test endpoints
curl http://localhost:8000/api/v1/templates/v1m1
```

**Render Deployment**:
```bash
# 1. Git commit + push
git add .
git commit -m "Feat: Hybrid template store with DB fallback"
git push origin main

# 2. Render auto-deploys

# 3. Run migration on production
# Option A: Add as Render "Build Command"
# Option B: Run manually via Supabase SQL Editor
# Option C: Run migration script via Render Shell
```

**Verificatie**:
```bash
# Check Render logs
[HYBRID] Trying database for template v1_mail1
[HYBRID] ✅ Template found in database
```

---

## 🔒 **ROLLBACK PLAN**

Als er problemen zijn na deployment:

### **Quick Rollback** (5 min)
```python
# In hybrid_template_service.py - Emergency toggle
FORCE_HARDCODED = os.getenv('FORCE_HARDCODED_TEMPLATES', 'false').lower() == 'true'

def get_template(self, template_id):
    if FORCE_HARDCODED:
        return get_hardcoded_template(template_id)  # Skip DB
    # ... normal hybrid logic
```

**Render Environment**:
```bash
FORCE_HARDCODED_TEMPLATES=true  # Emergency fallback
```

### **Full Rollback** (10 min)
```bash
# Revert git commit
git revert HEAD
git push origin main

# Render redeploys previous version
```

---

## 📊 **SUCCESS CRITERIA**

### **Functioneel**
- [ ] Alle 16 templates in Supabase database
- [ ] `GET /templates/v1m1` returns database template
- [ ] Template edit in Supabase → Zichtbaar in frontend (na refresh)
- [ ] Database template delete → Falls back to hard-coded
- [ ] Database connection failure → Falls back to hard-coded (no 500 error)

### **Performance**
- [ ] Response time < 200ms (met caching)
- [ ] No N+1 queries (bulk load templates)
- [ ] Graceful degradation bij DB slowness

### **Code Quality**
- [ ] Unit tests passed (90%+ coverage)
- [ ] No `USE_IN_MEMORY_STORES` checks in templates.py
- [ ] Comprehensive error logging
- [ ] Clean code - single responsibility principle

---

## 📁 **BESTANDSSTRUCTUUR**

**Nieuwe bestanden**:
```
backend/
├── scripts/
│   ├── seed_templates.sql          ← NEW (Database seed)
│   └── migrate_templates.py        ← NEW (Migration runner)
├── app/
│   └── services/
│       └── hybrid_template_service.py  ← NEW (Core hybrid logic)
└── tests/
    └── services/
        └── test_hybrid_template_service.py  ← NEW (Unit tests)
```

**Gewijzigde bestanden**:
```
backend/app/api/templates.py        ← UPDATE (Use hybrid service)
```

**Ongewijzigd** (blijft werken):
```
backend/app/core/templates_store.py     ✅ Hard-coded templates (fallback)
backend/app/core/template_id_normalizer.py  ✅ ID normalization
backend/app/services/testsend.py        ✅ Test email sending
```

---

## 🎯 **IMPLEMENTATIE VOLGORDE**

### **Fase 3A: Foundation** (1 uur)
1. ✅ Seed script schrijven (`seed_templates.sql`)
2. ✅ Migration script schrijven (`migrate_templates.py`)
3. ✅ Templates seeden in Supabase (via SQL Editor)
4. ✅ Verification: `SELECT COUNT(*) FROM templates;` → 16

### **Fase 3B: Hybrid Service** (1 uur)
1. ✅ `hybrid_template_service.py` implementeren
2. ✅ Unit tests schrijven
3. ✅ Local testing
4. ✅ Integration met Supabase client

### **Fase 3C: API Integration** (30 min)
1. ✅ Update `templates.py` (5 endpoints)
2. ✅ Verwijder `USE_IN_MEMORY_STORES` logic
3. ✅ Manual testing lokaal
4. ✅ Frontend testing (template detail/preview)

### **Fase 3D: Deployment** (30 min)
1. ✅ Git commit + push
2. ✅ Render deployment
3. ✅ Production testing
4. ✅ Monitor logs voor errors

---

## 🐛 **VERWACHTE ISSUES & OPLOSSINGEN**

### **Issue 1: Supabase Connection Timeout**
**Symptoom**: Slow API responses (>2s)  
**Oplossing**: Connection pooling + caching layer

### **Issue 2: Template Format Mismatch**
**Symptoom**: DB templates missing fields  
**Oplossing**: Strict schema validation in seed script

### **Issue 3: Cache Invalidation**
**Symptoom**: Template edits not visible immediately  
**Oplossing**: TTL cache (5 min) + manual refresh endpoint

### **Issue 4: Migration Race Condition**
**Symptoom**: Multiple seed runs create duplicates  
**Oplossing**: Use `ON CONFLICT` clause (idempotent)

---

## 📈 **TOEKOMSTIGE FEATURES** (Post Fase 3)

### **Template Editor UI** (Fase 4)
- Frontend CRUD voor templates
- WYSIWYG editor met placeholder preview
- Version history / rollback
- Template duplication

### **Template Validation** (Fase 5)
- Syntax checking (valid HTML)
- Placeholder validation (vars exist in leads)
- Asset validation (images exist)
- Preview before save

### **Template Analytics** (Fase 6)
- Open rates per template
- Click rates per template
- A/B testing support
- Performance metrics

---

## ✅ **CHECKLIST**

**Pre-Implementation**:
- [ ] Backup huidige Supabase database
- [ ] Test lokaal met testdata
- [ ] Review seed script met alle 16 templates
- [ ] Confirm Supabase connection credentials

**Implementation**:
- [ ] Seed script gemaakt en getest
- [ ] Migration script gerund (local + production)
- [ ] Hybrid service geïmplementeerd
- [ ] Templates API geüpdatet
- [ ] Unit tests geschreven en passed
- [ ] Local testing succesvol

**Post-Implementation**:
- [ ] Render deployment succesvol
- [ ] Production testing: alle endpoints werken
- [ ] Logs checken: geen errors
- [ ] Frontend testing: templates laden correct
- [ ] Performance check: response times < 200ms
- [ ] Document update in README

---

## 🎉 **EINDRESULTAAT**

**Voor Fase 3**:
```
Frontend → Templates API → Hard-coded Python
                           ❌ Niet editeerbaar
```

**Na Fase 3**:
```
Frontend → Templates API → Hybrid Service → 1. Database (editeerbaar)
                                            2. Hard-coded (fallback)
                           ✅ Editeerbaar + Zero downtime
```

**Benefits**:
- ✅ Templates editeerbaar zonder code deployment
- ✅ Zero downtime bij DB issues (fallback)
- ✅ Schaalbaar systeem (100+ templates mogelijk)
- ✅ Onafhankelijk van andere stores
- ✅ Performance (database query caching)
- ✅ Future-proof (template editor UI ready)

---

## 📞 **SUPPORT & VRAGEN**

**Als je tijdens implementatie problemen tegenkomt**:
1. Check Render logs voor specifieke errors
2. Verify Supabase connection (test query in SQL Editor)
3. Run unit tests lokaal: `pytest tests/services/test_hybrid_template_service.py`
4. Check fallback logic: Delete template from DB → Should still work

**Common Debugging Commands**:
```bash
# Check templates in database
SELECT id, name FROM templates ORDER BY version, mail_number;

# Test hybrid service locally
python -c "from app.services.hybrid_template_service import hybrid_template_service; print(hybrid_template_service.get_template('v1_mail1'))"

# Check Render logs
# Render Dashboard → Logs → Filter: [HYBRID]
```

---

**IMPLEMENTATIE READY! Start met Fase 3A. 🚀**
