# 📊 HUIDIGE STAND ANALYSE – Variabelen, Rapporten & Afbeeldingen

**Datum:** 2 oktober 2025  
**Versie:** 1.0  
**Doel:** Documenteren van de huidige implementatie van variabelen, rapporten en afbeeldingen in het Mail Dashboard project, en vergelijken met de vereisten uit `checklist_windsurf.md`.

---

## 1. VARIABELEN PER LEAD

### 1.1 Huidige Implementatie

#### **Backend: Lead Model**
- **Locatie:** `backend/app/models/lead.py`
- **Veld:** `vars: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))`
- **Type:** JSON dictionary voor flexibele opslag van custom variabelen
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Template Rendering System**
- **Locatie:** `backend/app/services/template_renderer.py`
- **Functionaliteit:**
  - Template renderer herkent 4 types variabelen:
    - `{{lead.*}}` - velden van de lead (email, company, url, domain)
    - `{{vars.*}}` - custom variabelen uit `lead.vars` dictionary
    - `{{campaign.*}}` - metadata van campagne
    - `{{image.*}}` - afbeeldingen (CID of URL)
  - Rendering met warnings voor ontbrekende variabelen
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Hard-coded Templates**
- **Locatie:** `backend/app/core/templates_store.py`
- **Aantal templates:** 16 (4 versies × 4 mails)
- **Gebruikte variabelen:**
  - `{{lead.company}}` - bedrijfsnaam
  - `{{lead.url}}` - website URL
  - `{{vars.keyword}}` - SEO zoekterm (custom)
  - `{{vars.google_rank}}` - huidige ranking (custom)
  - `{{image.cid 'dashboard'}}` - dashboard afbeelding
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Template Preview Service**
- **Locatie:** `backend/app/services/template_preview.py`
- **Functionaliteit:**
  - `extract_template_variables()` - extraheert alle variabelen uit template
  - `validate_lead_variables()` - valideert of lead alle vereiste variabelen heeft
  - Retourneert warnings voor ontbrekende variabelen
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Frontend: Lead Types**
- **Locatie:** `vitalign-pro/src/types/lead.ts`
- **Definitie:** `vars: Record<string, any>`
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **API Contract**
- **Endpoint:** `GET /leads`, `GET /leads/{id}`
- **Response bevat:** volledige `vars` object per lead
- **Preview endpoint:** `POST /previews/render` met `template_id` en `lead_id`
- **Status:** ✅ **GEÏMPLEMENTEERD**

### 1.2 Vergelijking met Checklist

#### ✅ **WAT ER WEL IS:**
1. Lead heeft `vars` property met custom variabelen
2. Templates kunnen variabelen gebruiken via `{{vars.*}}`
3. Template renderer detecteert en valideert variabelen
4. Warnings worden gegenereerd voor ontbrekende variabelen
5. Preview functionaliteit werkt met lead data

#### ❌ **WAT ER ONTBREEKT (volgens checklist):**
1. **Geen overzicht van ALLE template variabelen per lead**
   - Huidige implementatie: toont alleen variabelen die in de lead aanwezig zijn
   - Checklist vereist: toon alle 12 variabelen (of hoeveel het er zijn) met status "✅ gevuld" of "❌ ontbreekt"
   
2. **Geen "compleetheid indicator" in lead lijst**
   - Checklist vereist: badge "8/12" in tabel kolom
   - Huidige implementatie: alleen een badge met aantal aanwezige vars (`vars` count)

3. **Geen aggregatie van variabelen over alle templates heen**
   - Er is geen functie die alle unieke variabelen uit ALLE templates verzamelt
   - Er is geen service die berekent welke variabelen een lead "mist" voor volledige campagnes

4. **Geen filter op "compleetheid" in campagne wizard**
   - Checklist vereist: filter leads op "compleet" vs "incompleet"
   - Huidige implementatie: alleen filters op `has_var` (boolean voor enkele variabele)

---

## 2. RAPPORTEN KOPPELING

### 2.1 Huidige Implementatie

#### **Backend: Report Models**
- **Locatie:** `backend/app/models/report.py`
- **Tables:**
  - `reports` - metadata van rapporten (filename, type, size, storage_path, checksum)
  - `report_links` - koppeltabel tussen rapporten en leads/campagnes
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Report Store Service**
- **Locatie:** `backend/app/services/reports_store.py`
- **Functionaliteit:**
  - CRUD operaties voor rapporten
  - Link management (bind/unbind)
  - Query met filters (type, bound/unbound, search)
  - `get_report_for_lead(lead_id)` - haalt rapport op voor specifieke lead
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Bulk Upload**
- **API Endpoint:** `POST /reports/bulk?mode=by_image_key|by_email`
- **Functionaliteit:**
  - ZIP upload met meerdere rapporten
  - Automatische mapping op basis van:
    - `by_image_key` - match image_key met bestandsnaam
    - `by_email` - match email met bestandsnaam
  - Retourneert mapping resultaten (uploaded, failed, details)
- **Status:** ✅ **GEÏMPLEMENTEERD** (zoals beschreven in API)

#### **Report API**
- **Locatie:** `backend/app/api/reports.py`
- **Endpoints:**
  - `GET /reports` - lijst met filters
  - `POST /reports/upload` - single upload met optionele lead_id/campaign_id
  - `POST /reports/bulk` - bulk ZIP upload
  - `POST /reports/bind` - koppel rapport aan lead/campagne
  - `POST /reports/unbind` - ontkoppel rapport
  - `GET /reports/{id}/download` - download URL
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Frontend: Report Types**
- **Locatie:** `vitalign-pro/src/types/report.ts`
- **Types:**
  - `ReportItem` met `boundTo` property (kind: lead|campaign, id, label)
  - `BulkUploadResult` voor ZIP upload responses
  - `BulkMode` type: `'by_image_key' | 'by_email'`
- **Status:** ✅ **GEÏMPLEMENTEERD**

### 2.2 Vergelijking met Checklist

#### ✅ **WAT ER WEL IS:**
1. Report upload (single + bulk ZIP)
2. Koppeling via `by_email` of `by_image_key` (zoals checklist vereist)
3. Report links table voor many-to-many relaties
4. API endpoints voor bind/unbind
5. Bulk upload rapporteert matched/unmatched/ambiguous (conceptueel)

#### ❌ **WAT ER ONTBREEKT (volgens checklist):**
1. **Geen `has_report` indicator op Lead model**
   - Lead model heeft geen boolean field of computed property voor "heeft gekoppeld rapport"
   - Checklist vereist: `has_report` indicator (📄 icon of ✅/❌) in leads tabel

2. **Geen rapport preview in lead drawer**
   - Checklist vereist: sectie "Rapport" in lead detail met naam/status
   - Huidige lead detail: geen rapport informatie zichtbaar

3. **Geen fallback bij ontbrekende match**
   - Checklist vereist: "unmatched" of "ambiguous" status zichtbaar maken aan gebruiker
   - Huidige implementatie: onduidelijk hoe dit visueel getoond wordt

4. **Geen koppeling op `root_domain`**
   - Checklist noemt: "koppelen op basis van bestandsnaam = `root_domain` of `email`"
   - Huidige implementatie: alleen `by_image_key` en `by_email` modes
   - `root_domain` matching ontbreekt als optie

---

## 3. AFBEELDINGEN KOPPELING

### 3.1 Huidige Implementatie

#### **Backend: Asset Models**
- **Locatie:** `backend/app/models/lead.py`
- **Lead fields:**
  - `image_key: Optional[str] = None` - sleutel naar afbeelding in storage
- **Asset table:**
  - `assets` table met fields: id, key, mime, size, checksum, storage_path
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Asset Resolver Service**
- **Locatie:** `backend/app/services/asset_resolver.py`
- **Functionaliteit:**
  - `get_dashboard_image_path(domain)` - haalt dashboard afbeelding op basis van domein
  - Domain mapping: hard-coded (punthelder-marketing.nl → running_nl)
  - Naming convention: `{root_key}_picture.png`
- **Status:** ✅ **GEÏMPLEMENTEERD** (voor dashboard images)

#### **Template Rendering met Images**
- **Locatie:** `backend/app/services/template_renderer.py`
- **Functionaliteit:**
  - `{{image.cid 'hero'}}` - per-lead afbeelding via `image_key`
  - `{{image.cid 'dashboard'}}` - dashboard afbeelding via domein
  - `{{image.url 'logo'}}` - statische afbeelding URL
  - CID generation: `cid:{image_key}_{slot}` of `cid:dashboard_{domain}`
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Supabase Storage Integration**
- **API Endpoint:** `GET /assets/image-by-key?key=...`
- **Functionaliteit:** retourneert signed URL voor afbeelding (1 uur geldig)
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Bulk Upload voor Images**
- **Via Reports Tab:** ZIP upload met mode `by_image_key`
- **Matching logica:** bestandsnaam moet overeenkomen met `lead.image_key`
- **Status:** ✅ **GEÏMPLEMENTEERD** (via reports bulk upload)

### 3.2 Vergelijking met Checklist

#### ✅ **WAT ER WEL IS:**
1. Lead heeft `image_key` field
2. Asset storage met metadata (mime, size, checksum)
3. Template rendering ondersteunt per-lead images via CID
4. Bulk upload via ZIP met `by_image_key` matching
5. Signed URLs voor secure image access
6. Dashboard images via domain-based lookup

#### ❌ **WAT ER ONTBREEKT (volgens checklist):**
1. **Geen `has_image` indicator op Lead model**
   - Lead heeft wel `image_key` maar geen computed boolean `has_image`
   - Checklist vereist: 🖼️ icon of ✅/❌ indicator in leads tabel

2. **Geen image preview in lead drawer**
   - Checklist vereist: sectie "Afbeelding" met preview en fallback
   - Frontend heeft wel `ImagePreview` component maar onduidelijk of het gebruikt wordt in lead drawer
   - Lovable prompts (regel 54) noemen: "ImagePreview component met fallback"

3. **Geen visuele feedback bij ontbrekende match**
   - Checklist: "unmatched" of "ambiguous" status moet zichtbaar zijn
   - Huidige implementatie: onduidelijk hoe bulk upload failures worden getoond

---

## 4. DASHBOARD / UI AANPASSINGEN

### 4.1 Huidige Implementatie

#### **Leads Tabel**
- **Locatie:** `vitalign-pro/src/pages/leads/Leads.tsx`
- **Kolommen:** Email, Bedrijfsnaam, Domein/URL, Tags, Status, Laatst gemaild, Laatste open, Image key, Vars
- **Vars kolom:** Badge met count van variabelen
- **Status:** ✅ **GEÏMPLEMENTEERD** (basis versie)

#### **Lead Detail Drawer**
- **Componenten:**
  - `ImagePreview` component (vitalign-pro/src/components/leads/ImagePreview)
  - `JsonViewer` component (vitalign-pro/src/components/leads/JsonViewer)
- **Secties:** Basis info, afbeelding, variabelen (JSON), historie
- **Status:** ✅ **GEÏMPLEMENTEERD** (volgens Lovable prompts)

#### **Frontend Services**
- **Locatie:** `vitalign-pro/src/services/`
- **Services:** leads.ts, templates.ts, reports.ts, campaigns.ts, stats.ts, settings.ts, inbox.ts
- **API integratie:** Volledig geïmplementeerd met proper error handling
- **Status:** ✅ **GEÏMPLEMENTEERD**

### 4.2 Vergelijking met Checklist

#### ✅ **WAT ER WEL IS:**
1. Leads tabel met kolommen voor Email, Bedrijf, URL, Tags, Status
2. Vars kolom met badge (count)
3. Image key kolom aanwezig
4. Lead detail drawer met JSON viewer voor vars
5. ImagePreview component beschikbaar

#### ❌ **WAT ER ONTBREEKT (volgens checklist):**

**Leads Tabel - Kolommen:**
1. **"Vars" kolom moet "X/Y" tonen** (bijv. "8/12")
   - Huidige: toont alleen count van aanwezige vars
   - Checklist: toon aantal gevulde / totaal benodigd over alle templates

2. **"Image" kolom moet indicator tonen**
   - Checklist: 🖼️ icon of ✅/❌
   - Huidige: alleen `image_key` string waarde

3. **"Report" kolom ontbreekt volledig**
   - Checklist: nieuwe kolom met 📄 icon of ✅/❌
   - Huidige: geen rapport indicator in tabel

**Lead Detail Drawer - Secties:**
1. **"Variabelen" sectie moet alle template vars tonen**
   - Checklist: lijst met ALLE variabelen uit alle templates
   - Per variabele: ✅ gevuld of ❌ ontbreekt
   - Huidige: alleen JSON viewer met aanwezige vars

2. **"Afbeelding" sectie**
   - Checklist: preview met fallback indien ontbreekt
   - Huidige: component bestaat maar onduidelijk of correct geïntegreerd

3. **"Rapport" sectie ontbreekt**
   - Checklist: toon status + naam van gekoppeld rapport
   - Huidige: geen rapport sectie in drawer

---

## 5. CAMPAGNE SELECTIE & FILTERING

### 5.1 Huidige Implementatie

#### **Campaign API**
- **Locatie:** `backend/app/api/campaigns.py`
- **Create endpoint:** `POST /campaigns`
- **Payload:** `CampaignCreatePayload` met `audience` object
- **Audience filtering:** 
  - `filter` object voor algemene filters
  - `lead_ids` array voor specifieke leads
- **Status:** ✅ **GEÏMPLEMENTEERD** (basis)

#### **Lead Filters**
- **Query params:** `status`, `domain_tld`, `has_image`, `has_var`, `search`
- **Filtering logica:** `backend/app/services/leads_store.py`
- **Status:** ✅ **GEÏMPLEMENTEERD**

#### **Frontend Campaign Wizard**
- **Lovable prompts regel 172:** "4-staps Wizard (Basis → Doelgroep → Verzendregels → Review & Start)"
- **Doelgroep stap:** Lead selectie met filters
- **Status:** ✅ **GEÏMPLEMENTEERD** (volgens prompts)

### 5.2 Vergelijking met Checklist

#### ✅ **WAT ER WEL IS:**
1. Campaign wizard met doelgroep selectie
2. Lead filters (status, domain, has_image, has_var)
3. Bulk selectie vanuit leads tabel naar campagne

#### ❌ **WAT ER ONTBREEKT (volgens checklist):**

1. **"List" filter ontbreekt**
   - Checklist vereist: filter op `list_name` field
   - Lead model heeft geen `list_name` field
   - Geen API parameter voor list filtering

2. **"Compleetheid" filter ontbreekt**
   - Checklist vereist: filter alleen leads waarbij alle variabelen, rapport EN afbeelding aanwezig zijn
   - Huidige filters: alleen `has_image` en `has_var` (boolean)
   - Geen combined "is_complete" filter

3. **Geen voorvalidatie bij campagne start**
   - Checklist impliceert: voorkom onvolledige leads in campagne
   - Huidige implementatie: geen blocking validatie

---

## 6. TEMPLATE SYSTEEM & VARIABELEN

### 6.1 Alle Template Variabelen

**Uit analyse van `templates_store.py` (16 templates):**

#### **Standaard variabelen (alle templates):**
1. `{{lead.company}}` - bedrijfsnaam
2. `{{lead.url}}` - website URL

#### **Custom variabelen (alle templates):**
3. `{{vars.keyword}}` - SEO zoekterm
4. `{{vars.google_rank}}` - huidige ranking (in mails 1-3)

#### **Afbeeldingen (alle templates):**
5. `{{image.cid 'dashboard'}}` - dashboard screenshot

**Totaal unieke variabelen: 5**
- 2 lead fields
- 2 custom vars (waarvan 1 optioneel in mail 4)
- 1 image slot

### 6.2 Variabele Detectie Logica

#### **Bestaande functie:**
```python
# backend/app/services/template_preview.py
def extract_template_variables(template_content: str) -> Set[str]:
    """Extract all variables from template"""
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, template_content)
    # Returns: {'lead.company', 'lead.url', 'vars.keyword', 'vars.google_rank', 'image.cid'}
```

#### **Ontbrekende functionaliteit:**
- Geen functie die ALLE templates scant en unieke variabelen aggregeert
- Geen service die "required vars per versie" berekent
- Geen API die deze info exposed voor frontend

---

## 7. SAMENVATTING: WAT WERKT vs WAT ONTBREEKT

### ✅ **VOLLEDIG GEÏMPLEMENTEERD:**

1. **Lead variabelen opslag** - `vars` JSON field werkt
2. **Template rendering systeem** - alle variabele types worden herkend
3. **Hard-coded templates** - 16 templates met 5 unieke variabelen
4. **Report upload & linking** - single + bulk ZIP met email/image_key matching
5. **Asset storage** - image_key systeem met Supabase storage
6. **Dashboard images** - domain-based lookup voor screenshots
7. **API endpoints** - alle CRUD operaties voor leads, reports, assets
8. **Frontend components** - ImagePreview, JsonViewer, tabel met filters
9. **Campaign flow** - 4-staps wizard met lead selectie
10. **Preview functionaliteit** - template preview met warnings

### ⚠️ **GEDEELTELIJK GEÏMPLEMENTEERD:**

1. **Lead detail drawer** - componenten bestaan maar sectieverdeling onduidelijk
2. **Bulk upload feedback** - mapping logic bestaat maar UI feedback onduidelijk
3. **Lead filters** - basis filters werken maar niet alle vereiste filters

### ❌ **NIET GEÏMPLEMENTEERD (volgens checklist):**

#### **Variabelen:**
1. ❌ Aggregatie van alle template variabelen
2. ❌ "X/Y" compleetheid badge in leads tabel
3. ❌ Lijst met ✅/❌ per variabele in lead drawer
4. ❌ Service die berekent welke variabelen een lead mist
5. ❌ Filter op "compleetheid" in campagne wizard

#### **Rapporten:**
6. ❌ `has_report` computed property op Lead
7. ❌ Report kolom in leads tabel
8. ❌ Rapport sectie in lead drawer
9. ❌ Koppeling via `root_domain` (alleen email/image_key)

#### **Afbeeldingen:**
10. ❌ `has_image` computed property op Lead (alleen image_key check)
11. ❌ Image indicator kolom in leads tabel (alleen image_key tekst)
12. ❌ Image preview sectie in lead drawer (component bestaat maar integratie onduidelijk)

#### **Campagne Filtering:**
13. ❌ `list_name` field op Lead model
14. ❌ "List" filter in campagne wizard
15. ❌ Combined "is_complete" filter (vars + report + image)

---

## 8. CONCLUSIE

### 8.1 Architectuur Assessment

Het project heeft een **solide basis** met:
- Clean architecture (models, services, API layers)
- Flexibel variabelen systeem (JSON storage)
- Werkend template rendering systeem
- Complete CRUD operaties voor alle entiteiten

### 8.2 Gap Analysis

De **grote kloof** zit in:

1. **Gebruikersinzicht:** De applicatie heeft alle data, maar toont niet alle informatie die de gebruiker nodig heeft om een "complete" lead te identificeren
2. **Aggregatie logica:** Er is geen service die alle template variabelen verzamelt en per lead vergelijkt
3. **UI indicatoren:** Kolommen voor has_report en has_image ontbreken, vars kolom toont niet X/Y format
4. **Filtering:** Geen geavanceerde filters voor "complete" leads of list filtering

### 8.3 Impact op Workflow

**Huidige situatie:**
- Gebruiker ziet lead met vars: `{keyword: "SEO", google_rank: "15"}`
- Gebruiker weet NIET of dit alle benodigde variabelen zijn
- Gebruiker ziet NIET of er een rapport of afbeelding gekoppeld is (zonder in detail te kijken)

**Gewenste situatie (checklist):**
- Gebruiker ziet: "✅ Vars (2/2) | ✅ Image | ❌ Report"
- Gebruiker kan filteren: "Toon alleen complete leads"
- In detail drawer: lijst met alle 5 template variabelen + status

### 8.4 Implementatie Complexiteit

**Low complexity (1-2 dagen):**
- Toevoegen `has_report` en `has_image` computed properties
- UI kolommen toevoegen voor report/image indicators
- Lead drawer secties herstructureren

**Medium complexity (3-5 dagen):**
- Service bouwen voor template variabelen aggregatie
- "X/Y" badge logica implementeren
- Variabelen lijst met ✅/❌ in drawer
- List_name field toevoegen aan Lead model

**High complexity (5+ dagen):**
- Combined "is_complete" filter met multi-criteria
- Real-time compleetheid berekening bij import
- Bulk upload UI feedback voor unmatched/ambiguous
- Root_domain matching implementeren

---

## 9. AANBEVELINGEN

### Prioriteit 1 (Must Have voor MVP):
1. **Template variabelen service** - aggregeer alle unieke vars uit templates
2. **X/Y compleetheid badge** - toon in leads tabel
3. **Variabelen lijst in drawer** - alle vars met status ✅/❌
4. **Report/Image indicators** - kolommen in tabel + secties in drawer

### Prioriteit 2 (Should Have):
5. **List_name field** - toevoegen aan Lead model + filter
6. **Complete leads filter** - voor campagne doelgroep selectie
7. **Bulk upload feedback** - betere UI voor mapping resultaten

### Prioriteit 3 (Nice to Have):
8. **Root_domain matching** - als extra bulk mode
9. **Real-time validatie** - bij lead import
10. **Export incomplete leads** - CSV met ontbrekende data

---

**Document gegenereerd:** 2 oktober 2025, 20:55 CET  
**Analyse basis:** Code review van backend/ en vitalign-pro/, documentatie in README.md, API.md, IMPLEMENTATIONPLAN.md, checklist_windsurf.md, en implementatieplannen.

