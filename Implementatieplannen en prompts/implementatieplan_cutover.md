# 🛠️ Implementatieplan – Cut-over naar Live Data, Bestanden & Variabelen

## 📌 Doel
- **Alle mock/fixtures verwijderen** en volledig over op live API.
- **Bestandsconventies afdwingen**:
  - Reports: **PDF** met naam `{{root_domain}}_nl_report.pdf` (bijv. `cycle-ops_nl_report.pdf`).
  - Afbeeldingen: key `{{root_domain}}_picture`.
- **Variabelen** afdwingen + warnings in UI.
- **Zero-ambiguity** instructies voor Windsurf (frontend + backend).

Bronnen waarop dit plan is gebaseerd: Lovable-prompts (UI), API-specificatie, regels/afspraken, implementatiefasering, README.

---

## 1) Omgevingsconfig & Conventies

### 1.1 Frontend ENV
- `USE_FIXTURES=false` (of fixtures-code verwijderen).
- `API_BASE=/api/v1`
- Auth: **Supabase JWT** verplicht als `Authorization: Bearer <token>`.

### 1.2 API-Response Shape (uniform)
- Altijd `{ "data": ..., "error": null }` of `{ "data": null, "error": "message" }`.

### 1.3 Tijdzone
- Alle UI-tijden renderen in **Europe/Amsterdam**.

---

## 2) Frontend – Fixtures eruit, API erin

### 2.1 Services omschakelen
Vervang in:
- `services/leads.ts`, `services/campaigns.ts`, `services/templates.ts`, `services/reports.ts`, `services/stats.ts`, `services/settings.ts`  
alle fixture-calls door fetches naar de API-endpoints zoals gedefinieerd in **API.md**.

**Belangrijk**: keep UI-behavior (loading/empty/error/toasts) zoals de Lovable-prompts voorschrijven.

### 2.2 Routes (ongewijzigd, ter controle)
- Leads: `/leads`, `/leads/import`, detail drawer, importwizard (3 stappen), bulk selectie.
- Campagnes: `/campaigns`, `/campaigns/new`, `/campaigns/:id` + 4-staps wizard.
- Templates: `/templates`, `/templates/:id` + preview/testsend/warnings.
- Reports: `/reports`, `/reports/upload`, `/reports/bulk`.
- Stats: `/stats`.
- Settings: `/settings`.

---

## 3) Backend – Endpoints & Gedrag

### 3.1 Kern-endpoints (controleren/aanzetten)
- Leads:  
  - `GET /leads` (filters, paginatie), `GET /leads/{id}`, `POST /import/leads`.
- Templates:  
  - `GET /templates`, `GET /templates/{id}`,  
  - `GET /templates/{id}/preview?lead_id=...`, `POST /templates/{id}/testsend`.
- Campaigns:  
  - `GET /campaigns`, `POST /campaigns`, `GET /campaigns/{id}`,  
  - `POST /campaigns/{id}/pause|resume|stop`, `POST /campaigns/{id}/dry-run`.
- Reports:  
  - `GET /reports`, `POST /reports/upload`,  
  - `POST /reports/bulk?mode=by_image_key|by_email` (uitbreiden, zie 4.2),  
  - `POST /reports/bind`, `POST /reports/unbind`, `GET /reports/{id}/download`.
- Stats:  
  - `GET /stats/summary`, `GET /stats/export?scope=...`.
- Settings:  
  - `GET /settings`, `POST /settings` (partial).
- Assets:  
  - `GET /assets/image-by-key?key=...` retourneert signed URL.

---

## 4) Bestanden – Reports & Afbeeldingen

### 4.1 Afbeeldingen (image_key = `{{root_domain}}_picture`)
**Regel**  
- Voor elke lead zetten we `lead.image_key = root_domain + "_picture"`.

**Assets-service**  
- `GET /assets/image-by-key?key={key}` zoekt in Supabase Storage (bucket `images/`) naar `{key}.png|jpg|jpeg` en retourneert signed URL.  
- Frontend **ImagePreview** gebruikt deze URL, met fallback (zoals geëist in prompts).

**Herkomst**  
- Deze afbeeldingen komen uit de crawl/scraping resultaten (naamconventie sluit aan op `root_domain`)—geen extra mapping nodig.

### 4.2 Reports (PDF, bestandsnaam → lead-binding)
**Regel**  
- Rapporten zijn **altijd PDF** met filename `{{root_domain}}_nl_report.pdf` (case-insensitive).  
  Voorbeelden: `running_nl_report.pdf`, `cycle-ops_nl_report.pdf`.

**Bulk ZIP wizard gedrag (frontend)**  
- Mapping preview toont per file: `matched | unmatched | ambiguous` + reason.  
- Alleen **PDF** toegestaan; andere extensies → duidelijke client error + servervalidatie.

**Backend-koppeling**  
- **Uitbreiding** van `POST /reports/bulk`:
  - Voeg **mode=by_filename** toe (of implementeer als variant binnen bestaande mapping).
  - Extract `root` met regex: `^(?P<root>[a-z0-9._-]+)_nl_report$` (case-insensitive).
  - **Normaliseer**: lowercase, `_` → `-`, collapse `--`.
  - Bepaal lead `root_domain` (eerste label van FQDN zonder `www.`), identiek normaliseren.
  - Match `file_root == lead_root_domain` → bind (`POST /reports/bind`).
  - Geen match → `unmatched` met duidelijke `reason`.

**Resultaat**  
- `BulkUploadResult` blijft conform spec met mappingstatus en CSV-export in UI.

---

## 5) Import Wizard – Excel (scraping/crawl) → Leads

**Stap 1 (Upload)**  
- `.xlsx/.csv`, max 20MB, clientvalidaties actief.

**Stap 2 (Mapping)**  
- Map kolom `domain/url` → `lead.domain`.  
- Map `company/name` → `lead.company` (indien aanwezig).  
- Overige relevante kolommen → `vars.*` (vrij veld).  
- **Auto-hook** na mapping:  
  - `root_domain = to_root(lead.domain)`  
  - `lead.image_key = f"{root_domain}_picture"`  
- Preview 20 rijen; duplicates gemarkeerd.

**Stap 3 (Run)**  
- Start import → progress + toast + error-CSV.

---

## 6) Templates – Variabelen & Warnings

**Bronnen**  
- `lead.*`, `vars.*`, `campaign.*`.  
- Afbeelding CID: `{{image.cid 'hero'}}` → resolved via `lead.image_key`; bij ontbreken: 1×1 placeholder + **warning**.

**UI/Flow**  
- **Preview** en **Testsends** tonen **warnings** als variabelen of afbeelding ontbreken (blokkeert niet).  
- **Campaign Wizard – Review** herhaalt deze warnings voor de geselecteerde doelgroep.

---

## 7) E2E Validatie (moet slagen)

1. **Import** scraping/crawl `.xlsx`  
   - Leads verschijnen; elke lead met geldig domain heeft `image_key={{root_domain}}_picture`.  
2. **Assets**  
   - Lead-detail toont afbeelding via `/assets/image-by-key?key={{root_domain}}_picture` (fallback als niet aanwezig).  
3. **Reports Bulk**  
   - Upload `cycle-ops_nl_report.pdf` → automatisch gekoppeld aan lead `cycle-ops`.  
   - Niet-PDF → client- en serverfout met nette melding.  
4. **Templates Preview/Testsends**  
   - Voor lead `cycle-ops.nl`: **geen** missing-image warning (als image bestaat); variabele-warnings zichtbaar indien kolom ontbreekt.  
5. **Campaign Review**  
   - Warnings voor ontbrekende vars/images zichtbaar; Dry-run mogelijk (optioneel).

---

## 8) Acceptatiecriteria (Definition of Done)

- **Geen fixtures** meer: alle data via `/api/v1/*` met `{data,error}`-shape en JWT.  
- **Reports**:  
  - PDF-only; bestandsnaam → lead-binding via `{{root_domain}}_nl_report.pdf`.  
  - Bulkresultaat toont correcte matchstatus + CSV-export.  
- **Afbeeldingen**:  
  - `image_key={{root_domain}}_picture`; `/assets/image-by-key` levert signed URL of 404; UI toont fallback.  
- **Import**:  
  - Mapping-preview (20 rijen), duplicates gemarkeerd, auto `image_key` gezet.  
- **Templates**:  
  - Preview/Testsend met warnings voor missende vars/afbeelding; CID-placeholder als fallback.  
- **Wizard/Detail**:  
  - Review-pagina toont warnings; Campagne-detail heeft renders & logs conform prompts.  
- **Tijdzone**:  
  - Alle tijden in Europe/Amsterdam.

---

## 9) Referenties

- Lovable-prompts (UI-eisen & componentstructuur): Leads, Campagnes, Templates, Reports, Stats, Settings  
- API-specificatie (endpoints/payloads/shape): `/api/v1/*`  
- Rules (conventies, auth, logging, security)  
- Implementatieplan (fasering, MVP-scope)  
- README (architectuur & begrippen)

---

## 10) Appendix – Normalisatie & Matching (voorbeeld)

**Regex filename → root**  
```
^(?P<root>[a-z0-9._-]+)_nl_report$
```

**Normalisatie**  
- lowercase  
- `_` → `-`  
- collapse meerdere `-` naar één

**root_domain uit host**  
- strip `www.`  
- neem eerste label voor de TLD (bijv. `cycle-ops` uit `www.cycle-ops.nl`)

**Match**  
- `normalize(file_root) == normalize(root_domain)` → bind aan lead.

---

**Klaar.** Met dit plan is elk onderdeel gespecificeerd; Windsurf kan dit 1:1 implementeren zonder aannames.
