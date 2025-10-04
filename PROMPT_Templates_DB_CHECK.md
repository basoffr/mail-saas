# 📝 Prompt – Templates (DB-vereisten & variabelen-aggregatie)

Gebruik **Sonnet 4.5 Thinking**. Lees: `API.md`, `Lovable-prompts.md` (Templates), `HUIDIGE_STAND_ANALYSE.md`, `README.md`, `IMPLEMENTATIONPLAN.md`, `supabase_schema.sql`, `RULES.md`, relevante code (`services/template_renderer.py`, `services/template_preview.py`, `core/templates_store.py`).

> **Belangrijk:** **Onderzoek** de daadwerkelijke templates/renderer; documenteer afwijkingen van de documentatie.

## 🎯 Doelen
1. Bepaal wat DB nodig heeft om **universele variabelen** te kennen (alle templates → één set).
2. Bied mechaniek voor “X/Y completeness” per lead (alle templates samen).
3. Ondersteun preview/testsend (zonder DB-stress).

## 🔑 Context
- In alle flows komen steeds voor: `lead.email`, `lead.company`, `lead.url`, `vars.keyword`, `vars.google_rank`, `vars.seo_score`, `image_key` (dashboard), **rapport-link**.
- `template_variables` tabel in `supabase_schema.sql` seeded met deze keys (required=true).

## ✅ Te onderzoeken & opleveren
1. **Bron van waarheid**: Houd `template_variables` in DB of genereer runtime uit templates? Voor- en nadelen (performance, onderhoud).
2. **Completeness**: Check de view `lead_vars_completeness` en of X/Y correct is t.o.v. de gewenste set.
3. **Variabele-matrix**: Lever matrix (template × variable) als extra artefact om gaps te detecteren.
4. **Voorbeeldqueries**
   - Alle unieke variabelen (DB-gedreven vs. code-gedreven).
   - Completeness per lead (X/Y), lijst ontbrekende variabelen.
5. **Output**
   - **`TEMPLATES_DB_CHECK.md`** met advies (DB vs runtime), SQL-diff (indien nodig), matrix en **NEXT RESEARCH**.
