# 🌀 Windsurf Superprompt – Tabblad 1 (Leads)

Lees eerst zorgvuldig de volgende projectbestanden in:  
- `api.md`  
- `rules.md`  
- `readme.md`  
- `implementationplan.md`  
- `tab1_leads_implementatieplan.md`  
- `lovable-prompts.md`  
- `schema.md` (indien aanwezig)  

⚠️ Pas **uitsluitend code aan die relevant is voor Tabblad 1 (Leads)**.  
Andere modules (Campagnes, Templates, Rapporten, Statistieken, Instellingen) mogen **niet** aangepast worden.  

---

## ✅ Opdracht

### 1. Router & Endpoints
- Maak `api/leads.py` met endpoints exact volgens **API.md** en **tab1_leads_implementatieplan.md**:
  - `GET /leads` → filters: `status`, `domain_tld`, `has_image`, `has_var`; server-side paginatie.  
  - `GET /leads/{id}`.  
  - `POST /import/leads` → upload `.xlsx/.csv`; retourneer `{inserted, updated, skipped, jobId}`.  
  - `GET /assets/image-by-key?key=...` → signed URL stub.  
  - `POST /previews/render` → `{template_id, lead_id}` → `{html, text, warnings[]}`.  

- Conventies uit `rules.md`:  
  - Response shape `{data:..., error:null}`.  
  - Auth via Supabase JWT.  
  - Logging + telemetry events: `leads_import_started`, `leads_import_succeeded/failed`, `lead_viewed`, `lead_preview_rendered`.  

---

### 2. Modellen & Schemas
- Definieer SQLModel-tabellen:
  - **Lead**: `id (uuid)`, `email (unique, required)`, `company`, `url`, `domain`, `status (active|suppressed|bounced)`, `tags[]`, `image_key`, `last_emailed_at`, `last_open_at`, `vars (jsonb)`, `created_at`, `updated_at`.  
  - **Asset**: `id`, `key`, `mime`, `size`, `checksum`, `storage_path`, `created_at`.  
  - **ImportJob**: `id`, `filename`, `status`, `inserted`, `updated`, `skipped`, `errors (jsonb)`, `created_at`.  

- Constraints:
  - Unieke email in `leads`.  
  - Cascade waar logisch (bv. importjob → errors).  

- Definieer Pydantic schemas:  
  - `LeadOut`, `LeadDetail`, `ImportResult`, `AssetOut`.  
  - Consistent met API.md responses.  

---

### 3. Services
- **services/leads_import.py**:  
  - XLSX/CSV parser (pandas/openpyxl/csv).  
  - Mapping: verplicht email, optioneel url/company/image_key/image_url, overige kolommen → `vars.*`.  
  - Upsert-logica: insert, update (merge vars), skip duplicates.  
  - Rapportage: aantallen inserted/updated/skipped, max 50 inline fouten + CSV.  
  - Async job processing (APScheduler).  

- **services/template_preview.py**:  
  - Render context: `lead.*`, `vars.*`, `campaign.*`.  
  - Afbeeldingen: `{{image.cid 'slot'}}` → vervang door fake CID/placeholder.  
  - Retourneer `{html, text, warnings[]}`.  

---

### 4. Validaties & Beveiliging
- Bestandstype `.xlsx/.csv`, max 20MB.  
- Email regex + optionele MX-check.  
- Ongeldige rijen → skip + foutmelding.  
- Dubbele email binnen bestand → eerste houden, rest skippen.  
- Afbeeldingen: PNG/JPG ≤ 2MB; virus-scan stub.  
- Alleen geauthenticeerde users (JWT).  
- Audit: log importerende gebruiker + timestamp.  

---

### 5. Tests & Fixtures
- Schrijf pytest-tests voor alle endpoints:  
  - GET /leads (filters/paginatie/zoek).  
  - GET /leads/{id} (bestaand/niet-bestaand).  
  - POST /import/leads (valide bestand → inserted/updated/skipped; ongeldig bestand → nette fout).  
  - GET /assets/image-by-key (geldige/ongeldige key).  
  - POST /previews/render (valide lead+template → html/text; ontbrekende vars/afbeeldingen → warnings).  

- Fixtures: sample leads, import-bestand, templates.  
- Test coverage: ≥60% van leads-modules.  

---

### 6. Definition of Done
- Gebruiker kan `.xlsx/.csv` importeren, mapping doen, resultaten zien (inserted/updated/skipped + fouten).  
- Leads zichtbaar met filters/zoek en detaildrawer (vars JSON + image preview).  
- Template preview rendert HTML/text + warnings.  
- Alle endpoints volgen `api.md`.  
- Beveiliging, logging en telemetrie conform `rules.md`.  
- QA-checklist in `tab1_leads_implementatieplan.md` volledig groen.  

---
