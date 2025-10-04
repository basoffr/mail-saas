# 📣 Prompt – Campaigns (DB-vereisten & grondige check)

Gebruik **Sonnet 4.5 Thinking** en onderzoek de volledige campagne-flow. 
Lees: `API.md`, `Lovable-prompts.md` (Campaigns), `HUIDIGE_STAND_ANALYSE.md`, `README.md`, `IMPLEMENTATIONPLAN.md`, `supabase_schema.sql`, `RULES.md` en code (`backend/app/api/campaigns.py`, `services/*`, `vitalign-pro/src/pages/campaigns/*`).

> **Belangrijk:** Verricht **extra onderzoek** in code & services; documenteer elke discrepantie tussen docs en implementatie.

## 🎯 Doelen
1. Database-vereisten bevestigen voor: `campaigns`, `messages`, doelgroepselectie, follow-ups.
2. Filters: `list_name`, **`is_complete`**, suppressions/bounces, contacted last N days, one-per-domain.
3. SQL/queries die de wizard en detailpagina’s ondersteunen.

## 🔑 Context
- Campaign wizard (4 stappen) + detail met KPI’s/logs.
- Payload (API.md) voor create incl. audience filters & lead_ids.
- `messages` heeft unique `(campaign_id, lead_id)`, status flow, timestamps.
- Verzendvenster/throttle read-only uit `settings`.

## ✅ Te onderzoeken & opleveren
1. **Tabeldefinities**
   - `campaigns`: naam, `template_id`, `start_at`, `status`, `domains[]`, follow-up velden.
   - `messages`: FK’s, status, retry/bounce, unieke constraints.
2. **Doelgroepselectie**
   - Query “alleen complete leads” (`is_complete`), filter `list_name`.
   - Dedupe: suppressions/bounced, contacted last N days (met `last_emailed_at`), one-per-domain (SQL patroon!).
3. **Dry-run & planning**
   - Query om geplande aantallen per dag te simuleren (venster/throttle).
4. **Indexes & prestaties**
   - Op `messages.status/opened_at`, `campaigns.status/start_at`, domein-dedupe.
5. **Voorbeeldqueries**
   - Selectie doelgroep, resend failed, berichtenlog per campagne, KPI’s.
6. **Output**
   - **`CAMPAIGNS_DB_CHECK.md`** met veldenset, constraints, indexes, queries, **SQL-diff** en **NEXT RESEARCH**-blokken.
