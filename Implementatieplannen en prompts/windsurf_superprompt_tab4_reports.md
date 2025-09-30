# 🌀 Windsurf Superprompt – Tabblad 4 (Rapporten)

Lees eerst zorgvuldig de volgende projectbestanden in:  
- `api.md`  
- `rules.md`  
- `readme.md`  
- `implementationplan.md`  
- `tab4_rapporten_implementatieplan.md`  
- `lovable-prompts.md`  
- `schema.md` (indien aanwezig)  

⚠️ Pas **uitsluitend code aan die relevant is voor Tabblad 4 (Rapporten)**.  
Andere modules (Leads, Templates, Campagnes, Statistieken, Instellingen) mogen **niet** aangepast worden.  

---

## ✅ Opdracht

### 1. Router & Endpoints
- Maak `api/reports.py` met endpoints exact volgens **API.md** en **tab4_rapporten_implementatieplan.md**:
  - `GET /reports` → lijst met filters en paginatie.  
  - `POST /reports/upload` → multipart file + optioneel `{lead_id|campaign_id}`.  
  - `POST /reports/bulk?mode=by_image_key|by_email` → ZIP upload; retourneer mapping-resultaat.  
  - `POST /reports/bind` → `{report_id, lead_id|campaign_id}`.  
  - `POST /reports/unbind` → `{report_id}`.  
  - `GET /reports/{id}/download` → signed URL of binary.  

- Response-shape uit `rules.md` `{data:..., error:null}`.  
- Auth verplicht via Supabase JWT.  
- Logging events: `report_uploaded`, `report_bound`, `report_unbound`, `report_downloaded`.

---

### 2. Modellen & Schemas
- **Reports**:  
  - `id (uuid)`, `filename`, `type (pdf|xlsx|png|jpg)`, `size`, `storage_path`, `checksum`, `created_at`, `uploaded_by`.  
- **ReportLinks**:  
  - `report_id`, `lead_id (nullable)`, `campaign_id (nullable)`, `created_at`.  
- Constraints: rapport mag 1:1 gekoppeld zijn in MVP.  
- Pydantic schemas: `ReportItem`, `ReportUploadResponse`, `BulkUploadResult`.

---

### 3. Services
- **services/reports.py**:  
  - Upload: valideer bestandstype en max size (10MB).  
  - Bulk upload: ZIP max 100MB, ≤100 bestanden.  
  - Mapping logica:  
    - Mode by_image_key → match key ↔ bestand.  
    - Mode by_email → match bestandsnaam ↔ lead.email.  
    - Case-insensitive, extensie strippen.  
    - Ambiguous → status “ambiguous”, unmatched → status “unmatched”.  
  - Bind/unbind: check bestaan lead/campaign en rapport.  
  - Download: genereer signed URL, TTL 5 minuten.  

- Bestanden opslaan in Supabase bucket `reports/`.  
- Metadata in DB (`reports`, `report_links`).  

---

### 4. Validaties & Beveiliging
- Upload: alleen pdf/xlsx/png/jpg; max 10MB.  
- Bulk: ZIP max 100MB, max 100 files, unieke bestandsnamen.  
- Bind/unbind: valideer bestaan van entiteiten.  
- Download: alleen geauthenticeerde users; signed URL TTL 5m.  
- GDPR: rapporten kunnen PII bevatten → later retentiebeleid, nu log + markeer.  

---

### 5. Tests & Fixtures
- Pytest-tests:  
  - GET /reports: filters + paginatie.  
  - POST /reports/upload: geldig bestand → opgeslagen en gekoppeld. Ongeldig type/size → nette fout.  
  - POST /reports/bulk: valide ZIP → mapping-resultaat klopt.  
  - POST /reports/bind + unbind: koppelingen werken.  
  - GET /reports/{id}/download: signed URL geldig.  

- Fixtures: sample rapport (pdf), sample bulk-zip, sample leads + campaigns.  

---

### 6. Definition of Done
- Rapporten kunnen worden geüpload (single + bulk) en gekoppeld aan leads/campagnes.  
- Rapporten zichtbaar in lijst, filterbaar en downloadbaar.  
- Bulk mapping geeft correct resultaat (matched/unmatched/ambiguous).  
- Follow-ups kunnen optioneel rapport meesturen.  
- Logging, auth en telemetrie conform rules.md.  
- QA-checklist in `tab4_rapporten_implementatieplan.md` volledig groen.  

---
