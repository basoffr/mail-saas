# 🔧 IMPLEMENTATIEPLAN - Variabelen, Rapporten & Afbeeldingen

**Datum:** 2 oktober 2025  
**Basis:** HUIDIGE_STAND_ANALYSE.md + checklist_windsurf.md  
**Doel:** Stapsgewijze implementatie van ontbrekende features

---

## 📋 OVERZICHT WIJZIGINGEN

### Backend (Python/FastAPI)
1. Template variabelen aggregatie service
2. Lead model uitbreiden: `list_name`, computed properties
3. Lead enrichment service (has_report, has_image, completeness)
4. API response schemas aanpassen

### Frontend (React/TypeScript)
1. Leads tabel: nieuwe kolommen (vars X/Y, image, report)
2. Lead drawer: nieuwe secties (vars lijst, image preview, report info)
3. Campagne filters: list_name, is_complete

---

## 🎯 FASE 1: BACKEND - TEMPLATE VARIABELEN SERVICE

### Stap 1.1: Template Variables Aggregator
**Bestand:** `backend/app/services/template_variables.py` (NIEUW)

```python
from typing import Set, List, Dict
from app.core.templates_store import get_all_templates

class TemplateVariablesService:
    def get_all_required_variables(self) -> Set[str]:
        """Aggregeer alle unieke variabelen uit alle templates"""
        # Scan alle 16 templates
        # Return: {'lead.company', 'lead.url', 'vars.keyword', 'vars.google_rank', 'image.cid'}
        
    def get_missing_variables(self, lead_vars: Dict, lead_image_key: str) -> List[str]:
        """Bepaal welke variabelen een lead mist"""
        
    def calculate_completeness(self, lead) -> Dict:
        """Return: {filled: 4, total: 5, missing: ['vars.google_rank']}"""
```

### Stap 1.2: Lead Enrichment Service  
**Bestand:** `backend/app/services/lead_enrichment.py` (NIEUW)

```python
def enrich_lead_with_metadata(lead, reports_store, template_vars_service):
    """Voeg computed fields toe aan lead response"""
    return {
        **lead.__dict__,
        'has_report': reports_store.get_report_for_lead(lead.id) is not None,
        'has_image': lead.image_key is not None and lead.image_key != '',
        'vars_completeness': template_vars_service.calculate_completeness(lead),
        'is_complete': check_if_complete(lead, reports_store, template_vars_service)
    }
```

---

## 🎯 FASE 2: BACKEND - LEAD MODEL UITBREIDING

### Stap 2.1: Lead Model  
**Bestand:** `backend/app/models/lead.py`

**Toevoegen:**
```python
list_name: Optional[str] = Field(default=None, index=True)
```

### Stap 2.2: Lead Schema  
**Bestand:** `backend/app/schemas/lead.py`

**LeadOut uitbreiden:**
```python
class LeadOut(BaseModel):
    # ... bestaande fields
    list_name: Optional[str] = None
    has_report: bool = False
    has_image: bool = False
    vars_completeness: Dict[str, Any] = {}  # {filled: 4, total: 5, missing: [...]}
    is_complete: bool = False
```

---

## 🎯 FASE 3: BACKEND - API AANPASSINGEN

### Stap 3.1: Leads API  
**Bestand:** `backend/app/api/leads.py`

**GET /leads aanpassen:**
- Integreer lead_enrichment_service
- Voeg filter toe: `list_name`, `is_complete`

**GET /leads/{id} aanpassen:**
- Return enriched lead met alle metadata

### Stap 3.2: Template Variables Endpoint (NIEUW)
**Endpoint:** `GET /templates/variables`
```python
@router.get("/templates/variables")
async def get_all_template_variables():
    """Return alle unieke variabelen over alle templates"""
    return {"data": {
        "variables": list(template_vars_service.get_all_required_variables()),
        "total": 5
    }}
```

---

## 🎯 FASE 4: FRONTEND - TYPES & SERVICES

### Stap 4.1: Lead Types  
**Bestand:** `vitalign-pro/src/types/lead.ts`

```typescript
export interface Lead {
  // ... bestaande fields
  listName?: string;
  hasReport: boolean;
  hasImage: boolean;
  varsCompleteness: {
    filled: number;
    total: number;
    missing: string[];
  };
  isComplete: boolean;
}
```

### Stap 4.2: Leads Service  
**Bestand:** `vitalign-pro/src/services/leads.ts`

**LeadsQuery uitbreiden:**
```typescript
export interface LeadsQuery {
  // ... bestaande
  listName?: string;
  isComplete?: boolean;
}
```

---

## 🎯 FASE 5: FRONTEND - LEADS TABEL

### Stap 5.1: Leads.tsx Kolommen  
**Bestand:** `vitalign-pro/src/pages/leads/Leads.tsx`

**Nieuwe kolommen toevoegen:**
1. **Vars:** Badge met "4/5" format (ipv alleen count)
2. **Image:** Icon indicator (🖼️ ✅ of ❌)  
3. **Report:** Icon indicator (📄 ✅ of ❌)

```tsx
<TableCell>
  <Badge variant={lead.varsCompleteness.filled === lead.varsCompleteness.total ? "default" : "secondary"}>
    {lead.varsCompleteness.filled}/{lead.varsCompleteness.total}
  </Badge>
</TableCell>
<TableCell>{lead.hasImage ? '🖼️ ✅' : '❌'}</TableCell>
<TableCell>{lead.hasReport ? '📄 ✅' : '❌'}</TableCell>
```

---

## 🎯 FASE 6: FRONTEND - LEAD DRAWER

### Stap 6.1: Variabelen Sectie  
**Component:** Nieuwe sectie in drawer

```tsx
<div className="space-y-2">
  <h3>Variabelen ({lead.varsCompleteness.filled}/{lead.varsCompleteness.total})</h3>
  {allTemplateVars.map(varName => (
    <div key={varName} className="flex items-center gap-2">
      {hasVariable(lead, varName) ? '✅' : '❌'}
      <span>{varName}</span>
      {hasVariable(lead, varName) && <code>{getVarValue(lead, varName)}</code>}
    </div>
  ))}
</div>
```

### Stap 6.2: Image Sectie  
**Gebruik bestaande ImagePreview component**

```tsx
<div>
  <h3>Afbeelding</h3>
  {lead.hasImage ? (
    <ImagePreview imageKey={lead.imageKey} />
  ) : (
    <div className="text-muted">Geen afbeelding gekoppeld</div>
  )}
</div>
```

### Stap 6.3: Report Sectie (NIEUW)  
**Component:** Rapport info + download link

```tsx
<div>
  <h3>Rapport</h3>
  {lead.hasReport ? (
    <div>
      <FileIcon />
      <span>{report.filename}</span>
      <Button onClick={handleDownload}>Download</Button>
    </div>
  ) : (
    <div className="text-muted">Geen rapport gekoppeld</div>
  )}
</div>
```

---

## 🎯 FASE 7: FRONTEND - CAMPAGNE FILTERS

### Stap 7.1: Campaign Wizard - Doelgroep Stap  
**Bestand:** Campaign wizard component

**Nieuwe filters:**
```tsx
<Select>
  <SelectTrigger>List</SelectTrigger>
  <SelectContent>
    {uniqueListNames.map(name => <SelectItem value={name}>{name}</SelectItem>)}
  </SelectContent>
</Select>

<Checkbox checked={onlyCompleteLeads} onChange={setOnlyCompleteLeads}>
  Alleen complete leads (alle vars + rapport + image)
</Checkbox>
```

---

## 🎯 FASE 8: TESTING

### Backend Tests
**Bestand:** `backend/app/tests/test_template_variables.py` (NIEUW)
- Test get_all_required_variables()
- Test calculate_completeness()
- Test lead enrichment

**Bestand:** `backend/app/tests/test_leads_api.py` (UPDATE)
- Test nieuwe filters (list_name, is_complete)
- Test enriched response fields

### Frontend Tests
- Component tests voor nieuwe kolommen
- Service tests voor enriched lead data

---

## 📅 IMPLEMENTATIE VOLGORDE

### Week 1 - Backend Foundation
1. ✅ Template variables service
2. ✅ Lead enrichment service
3. ✅ Lead model + schema updates
4. ✅ API endpoint updates
5. ✅ Backend tests

### Week 2 - Frontend Implementation
6. ✅ Types + services update
7. ✅ Leads tabel kolommen
8. ✅ Lead drawer secties
9. ✅ Campagne filters
10. ✅ Frontend integration tests

### Week 3 - Polish & Deploy
11. ✅ Code review
12. ✅ Documentation
13. ✅ Deployment
14. ✅ User acceptance testing

---

## ✅ ACCEPTANCE CRITERIA

**Variabelen:**
- [ ] Tabel toont "4/5" badge voor vars
- [ ] Drawer toont lijst met alle 5 template vars + ✅/❌ status
- [ ] API retourneert vars_completeness object

**Rapporten:**
- [ ] Tabel toont 📄 ✅/❌ indicator
- [ ] Drawer toont rapport sectie met naam/download
- [ ] has_report computed correct

**Afbeeldingen:**
- [ ] Tabel toont 🖼️ ✅/❌ indicator
- [ ] Drawer toont image preview met fallback
- [ ] has_image computed correct

**Filters:**
- [ ] List filter werkt in campagne wizard
- [ ] "Complete leads only" filter werkt
- [ ] Filters combineerbaar

---

**Einde implementatieplan**
