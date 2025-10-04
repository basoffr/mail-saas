# 📊 Prompt – Stats (DB-vereisten, aggregaties & performance)

Gebruik **Sonnet 4.5 Thinking**. Lees: `API.md`, `Lovable-prompts.md` (Stats), `supabase_schema.sql`, `README.md`, relevante backend code (`services/stats*`, `api/stats.py`).

> **Belangrijk:** **Onderzoek** aggregaties en performance. Documenteer aannames en alternatieven (views vs. materialized views).

## 🎯 Doelen
1. Definieer queries/views voor: global KPI’s, timeline per dag, per domain, per campagne.
2. Beoordeel indexes en refresh-strategie voor performance.

## 🔑 Context
- Brondatasets: `messages`, `opens`, (optioneel) `suppressions`/bounces.
- UI wil CSV export.

## ✅ Te onderzoeken & opleveren
1. **Views/Queries**
   - Global: totalSent, openRate, bounces.
   - Timeline: sent/opens per dag (UTC→presentatie in Europe/Amsterdam).
   - Per domain/campaign tabellen.
2. **Indexes & MV’s**
   - Waar zinvol materialized views + refresh interval.
3. **Output**
   - **`STATS_DB_CHECK.md`** met definitieve SQL, indexplan, MV-plan, **NEXT RESEARCH**.
