# 🌀 Windsurf Superprompt – Tabblad 2 (Templates)

Lees eerst zorgvuldig de volgende projectbestanden in:  
- `api.md`  
- `rules.md`  
- `readme.md`  
- `implementationplan.md`  
- `tab2_templates_implementatieplan.md`  
- `lovable-prompts.md`  
- `schema.md` (indien aanwezig)  

⚠️ Pas **uitsluitend code aan die relevant is voor Tabblad 2 (Templates)**.  
Andere modules (Leads, Campagnes, Rapporten, Statistieken, Instellingen) mogen **niet** aangepast worden.  

---

## ✅ Opdracht

### 1. Router & Endpoints
- Maak `api/templates.py` met endpoints exact volgens **API.md** en **tab2_templates_implementatieplan.md**:
  - `GET /templates` → lijst van templates (id, name, subject, updated_at, required_vars[]).  
  - `GET /templates/{id}` → detail (body_html/body_text, variabelenschema, slots, assets).  
  - `GET /templates/{id}/preview?lead_id=...` → render template met lead-data, retourneer `{html, text, warnings[]}`.  
  - `POST /templates/{id}/testsend` → payload `{to, leadId?}` → verstuur testmail via mailer (SMTP stub).  

- Response-shape uit `rules.md` `{data:..., error:null}`.  
- Auth verplicht via Supabase JWT.  
- Logging events: `template_preview_requested`, `template_preview_warned`, `template_testsend_requested`, `template_testsend_sent`, `template_testsend_failed`.

---

### 2. Modellen & Schemas
- Definieer SQLModel-tabel `Template`:  
  - `id (uuid)`, `name`, `subject_template`, `body_template`, `updated_at`, `required_vars[] (jsonb)`, `assets[] (jsonb, optioneel)`.  
- Hard-code seedtemplates voor MVP (zie readme).  
- Pydantic schemas:  
  - `TemplateOut`, `TemplateDetail`, `TemplatePreviewResponse`, `TestsendPayload`.

---

### 3. Services
- **services/template_renderer.py**:  
  - Engine ondersteunt:  
    - Interpolatie `{{ lead.email }}`, `{{ vars.score }}`, `{{ campaign.name }}`.  
    - Helpers: `default`, `uppercase`, `lowercase`, `if`.  
    - Afbeeldingen:  
      - `{{image.cid 'slot'}}` → resolve naar lead.image_key of placeholder.  
      - `{{image.url 'logo'}}` → vaste asset-URL.  
  - Validatie:  
    - Verzamel missende variabelen → warnings[].  
    - Onderwerp na render niet leeg, max 255 chars.  
  - Output: `{html, text, warnings[]}`.

- **services/testsend.py**:  
  - Queue testmails met hoge prioriteit.  
  - Respecteer provider-throttle (SMTP stub nu).  
  - Voeg altijd unsubscribe-header toe (standaardtekst).  
  - Logging van resultaat (ok/error).

---

### 4. Validaties & Beveiliging
- Preview:  
  - Lead moet bestaan, status ≠ suppressed/bounced → waarschuwing tonen.  
  - Ontbrekende per-lead afbeelding → placeholder + warning.  
- Testsend:  
  - `to` moet geldig emailadres zijn.  
  - 5 testsends/min per gebruiker (rate-limit).  
  - Fout SMTP/provider → nette foutmelding + log raw error.  
- Auth verplicht (JWT).  
- Logging nooit volledige mailbody, alleen hash/IDs + status.

---

### 5. Tests & Fixtures
- Pytest-tests voor alle endpoints:  
  - GET /templates → lijst laadt.  
  - GET /templates/{id} → detail juist.  
  - GET /templates/{id}/preview → correcte render + warnings.  
  - POST /templates/{id}/testsend → valide adres → ok; fout adres → nette fout.  

- Fixtures:  
  - Sample templates (met variabelen + afbeeldingen).  
  - Sample leads voor preview.  
  - Fake SMTP mock voor testsend.  

---

### 6. Definition of Done
- Templates zichtbaar in UI (list/detail).  
- Preview rendert HTML + text, toont warnings bij missende variabelen of afbeeldingen.  
- Testsend stuurt mail naar opgegeven adres met unsubscribe-header.  
- Endpoints conform API.md, logging & auth conform rules.md.  
- QA-checklist in `tab2_templates_implementatieplan.md` volledig groen.  

---
