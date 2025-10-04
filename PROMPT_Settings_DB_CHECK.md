# ⚙️ Prompt – Settings (DB-vereisten & singleton)

Gebruik **Sonnet 4.5 Thinking**. Lees: `API.md`, `Lovable-prompts.md` (Settings), `supabase_schema.sql`, `RULES.md`, `README.md`, relevante backend code (`api/settings.py`, `models/settings.py`).

> **Belangrijk:** **Onderzoek** of de singleton-aanpak voldoet en waar normalisatie zinnig is.

## 🎯 Doelen
1. Valideer of alle settings velden aanwezig zijn (venster, throttle, domains, unsubscribe, tracking pixel, DNS, email infra).
2. Bepaal of normalisatie nodig is (bijv. domains aparte tabel) of TTL voor signed URLs ergens moet worden opgeslagen.

## ✅ Te onderzoeken & opleveren
1. **Model & constraint**
   - Singleton (`id=1`) + validatie; migratiepad.
2. **Uitbreidingen**
   - Domains normalisatie ja/nee; provider toggles.
3. **Output**
   - **`SETTINGS_DB_CHECK.md`** met confirmaties, eventuele migraties en **NEXT RESEARCH**.
