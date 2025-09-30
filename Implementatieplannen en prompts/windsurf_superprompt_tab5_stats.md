# 🌀 Windsurf Superprompt – Tabblad 5 (Statistieken)

Lees eerst zorgvuldig de volgende projectbestanden in:  
- `api.md`  
- `rules.md`  
- `readme.md`  
- `implementationplan.md`  
- `tab5_statistieken_implementatieplan.md`  
- `lovable-prompts.md`  
- `schema.md` (indien aanwezig)  

⚠️ Pas **uitsluitend code aan die relevant is voor Tabblad 5 (Statistieken)**.  
Andere modules (Leads, Templates, Campagnes, Rapporten, Instellingen) mogen **niet** aangepast worden.  

---

## ✅ Opdracht

### 1. Router & Endpoints
- Maak `api/stats.py` met endpoints exact volgens **API.md** en **tab5_statistieken_implementatieplan.md**:
  - `GET /stats/summary?from=YYYY-MM-DD&to=YYYY-MM-DD&template_id?`  
    → retourneer `{global, domains[], campaigns[], timeline{sentByDay[], opensByDay[]}}`.  
  - `GET /stats/export?scope=global|domain|campaign&from=...&to=...&id?`  
    → genereer CSV-export.  
  - Optioneel: `GET /stats/domains` en `GET /stats/campaigns` (voor losse tabellen).

- Response-shape uit `rules.md` `{data:..., error:null}`.  
- Auth verplicht via Supabase JWT.  
- Logging events: `stats_viewed`, `stats_exported`.

---

### 2. Modellen & Schema
- Gebruik `messages`-tabel als bron:  
  - `id`, `campaign_id`, `lead_id`, `domain_used`, `sent_at`, `open_at`, `status (queued|sent|bounced|opened|failed)`, `last_event_at`.  
- Eventueel `message_events` (optioneel).  
- Pydantic schemas: `StatsSummary`, `GlobalStats`, `DomainStats`, `CampaignStats`, `TimelinePoint`.

---

### 3. Services
- **services/stats.py**:  
  - SQL-queries voor aggregaties:  
    - Global: total_sent, total_opens, open_rate, bounces.  
    - Timeline: sent_by_day[], opens_by_day[].  
    - Per domein: gegroepeerd op domain_used.  
    - Per campagne: gegroepeerd op campaign_id.  
  - CSV export helper: consistente headers, komma-gescheiden, datums ISO (`YYYY-MM-DD`).  
  - Optioneel caching (bijv. 60s) voor summary.

---

### 4. Validaties & Beveiliging
- Datumbereik: `from ≤ to`, max 365 dagen.  
- Lege datasets → return lege waarden (geen error).  
- Auth verplicht (JWT).  
- Data scope: single-tenant, geen cross-org leaks.  
- Exports: geen PII → alleen domeinnamen & campagnenamen.  

---

### 5. Tests & Fixtures
- Pytest-tests:  
  - Global KPI’s binnen range correct.  
  - Timeline berekeningen kloppen.  
  - Per domein & campagne aggregaties kloppen.  
  - Export CSV valide headers + inhoud.  
  - Edge cases: leeg bereik, geen data, weekend-only bereik.  

- Fixtures:  
  - Sample messages (sent, opened, bounced).  
  - Sample campagnes + domeinen.

---

### 6. Definition of Done
- Statistieken-tab toont correcte global totals, per domein en per campagne.  
- Timeline-grafieken renderen consistent met totals.  
- CSV-export werkt voor alle scopes.  
- Performance: summary-call <700ms bij 2.1k messages, export <3s.  
- Logging, auth en telemetrie conform rules.md.  
- QA-checklist in `tab5_statistieken_implementatieplan.md` volledig groen.  

---
