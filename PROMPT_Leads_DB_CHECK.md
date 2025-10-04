# 🔎 Prompt – Leads (DB-vereisten & grondige check)

Gebruik **Sonnet 4.5 Thinking**. Dit is een grondige controle voor het tabblad **Leads**. 
Lees en cross-check minimaal deze bronnen in de repository:
- `README.md` – architectuur & MVP-scope
- `IMPLEMENTATIONPLAN.md` – fasering en functionele scope
- `API.md` – endpoints, query params, response shapes
- `Lovable-prompts.md` – UI-eisen & kolommen voor Leads
- `HUIDIGE_STAND_ANALYSE.md` – wat is al aanwezig vs. wat mist
- `checklist_windsurf.md` – vereisten voor variabelen/rapporten/afbeeldingen per lead
- `supabase_schema.sql` – huidig (voorstel) schema, views en indexes
- Codepaden: `backend/app/models/*`, `backend/app/api/leads.py`, `backend/app/services/*`, `vitalign-pro/src/pages/leads/*`, `vitalign-pro/src/components/leads/*`, `vitalign-pro/src/services/leads.ts`

> **Belangrijk:** Ga uit van mogelijke discrepanties tussen docs en code. **Doe aanvullend onderzoek** in de codebase. Noteer alle inconsistenties expliciet.

## 🎯 Doelen
1. **Inventariseer alle DB-vereisten** voor Leads (velden, relaties, constraints, indexes, views).
2. **Valideer** of import (Excel), afbeeldingen (ZIP), rapporten (ZIP) correct kunnen koppelen aan Leads.
3. **Bepaal** welke extra SQL/migraties nodig zijn t.o.v. `supabase_schema.sql`.
4. **Voorzie voorbeeldqueries** voor de UI (paginated list, filters, lead-detail).

## 🔑 Context en bekende eisen (ter referentie)
- Minimale dataset per lead (vereist voor alle templates):  
  `lead.email`, `lead.company`, `lead.url`, `vars.keyword`, `vars.google_rank`, `vars.seo_score`, `image_key` (dashboard image), **rapport-koppeling** (via `report_links`).  
- UI kolommen (volgens prompts): Email, Bedrijf, Domein/URL, Tags, Status, Laatst gemaild, Laatste open, **Image indicator**, **Report indicator**, **Vars X/Y**.
- Views voorgesteld in schema:  
  `lead_report_status (has_report)`, `lead_image_status (has_image)`, `lead_vars_completeness (total/present)`, **`leads_enriched`** (samengevoegd, incl. `is_complete`).

## ✅ Te onderzoeken & opleveren
1. **Velden Leads**
   - Vereist: `email (unique)`, `company`, `url`, `domain`, `root_domain`, `image_key`, `list_name`, `tags[]`, `status`, `vars jsonb`, `last_emailed_at`, `last_open_at`.
   - Controleer of `root_domain` en `domain` consistent gevuld worden (import/parsers). Geef voorbeeld-normalisatie.
2. **Relaties**
   - Image-koppeling via `image_key` → `assets.key` (of presence-only via key).
   - Rapport-koppeling via `report_links.lead_id`.
3. **Indicatoren & views**
   - Bevestig of `has_report`, `has_image`, `present_required/total_required`, `is_complete` beschikbaar zijn via views óf materialized views (performance). 
4. **Indexes & constraints**
   - Check unique, FK’s, cascade, en indexes op `root_domain`, `list_name`, `status`, timestamps.
5. **Voorbeeldqueries (lever exact SQL)**
   - Paginated & filtered select op `leads_enriched` (met zoek/sort/filter).
   - Eén lead detail met alle indicatoren + vars JSON.
   - “Incomplete leads” export (alle ontbrekende velden).
6. **Excel import mapping**
   - Voorbeeld mapping-tabel: kolomnaam → DB-veld/JSON key (inclusief `list_name`).
7. **Output**
   - **`LEADS_DB_CHECK.md`** met:
     - Definitieve veldenset + rationale
     - Relaties & views (welke kies je en waarom)
     - SQL-diff t.o.v. `supabase_schema.sql`
     - Voorbeeldqueries (copy/paste klaar)
     - Open vragen (wat moet nog verder onderzocht worden?)

> **Nadruk:** Waar feiten ontbreken of code afwijkt, **documenteer de hiaten** en markeer als **NEXT RESEARCH** met concrete vervolgstappen.
