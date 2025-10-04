# 📂 Prompt – Reports (DB-vereisten, bulk mapping & statusweergave)

Gebruik **Sonnet 4.5 Thinking**. Lees: `API.md`, `Lovable-prompts.md` (Reports), `HUIDIGE_STAND_ANALYSE.md`, `supabase_schema.sql`, `README.md`, relevante backend code (`api/reports.py`, `services/reports_store.py`).

> **Belangrijk:** **Onderzoek** matching-modi, UI-feedback en edge cases. Documenteer hiaten.

## 🎯 Doelen
1. Valideer tabellen `reports` en `report_links` + bulk ZIP flows.
2. Ondersteun matching op `by_email`, `by_image_key` en (optioneel) `by_root_domain`.
3. Lever UI-queries voor indicators `has_report` en lead drawer-informatie.

## 🔑 Context
- ZIP upload modes: `by_image_key` (images), `by_email` (reports); wens: `by_root_domain`.
- Indicatoren in UI: 📄 **has_report** per lead + detail sectie.

## ✅ Te onderzoeken & opleveren
1. **Datamodel**
   - Bevestig velden en constraints (`unique`, cascade). 
2. **Indexes**
   - Voor snelle bulk mapping (filename, uploaded_at, type) en lookup per lead/campaign.
3. **Matching-algoritmen**
   - Pseudocode + SQL snippets voor elk mode; ambiguous/unmatched casus loggen.
4. **Voorbeeldqueries**
   - Per lead “laatste rapport”, lijst unmatched, download (signed URL).
5. **Output**
   - **`REPORTS_DB_CHECK.md`** met SQL-diff (incl. `by_root_domain` ondersteuning indien nodig) en **NEXT RESEARCH**.
