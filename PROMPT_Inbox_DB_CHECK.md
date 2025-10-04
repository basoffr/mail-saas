# 📥 Prompt – Inbox (DB-vereisten, linking & security)

Gebruik **Sonnet 4.5 Thinking**. Lees: `README.md`, `API.md`, `HUIDIGE_STAND_ANALYSE.md`, `RULES.md`, `supabase_schema.sql` en code (zoek naar `inbox*`, `imap*`, `pop3*`, `reply*`).  
> Inbox valt mogelijk **buiten MVP** → behandel als **feature-flag**. **Meer onderzoek** is noodzakelijk naar daadwerkelijke code & infra.

## 🎯 Doelen
1. Datamodel schetsen voor inbound mail (accounts, messages, attachments, threads).
2. Koppeling naar outbound `messages` en `leads` (Reply tracking).
3. Security voor secrets (geen plaintext), PII-minimalisatie.

## ✅ Te onderzoeken & opleveren
1. **Tabelvoorstellen**
   - `inbox_accounts`, `inbox_messages`, `inbox_attachments`, `message_threads`.
2. **Linking**
   - Koppelen via `In-Reply-To`/`References` → outbound message; fallback op e-mail matching.
3. **Views & queries**
   - `inbox_enriched` + voorbeelden: ongelezen, gereplyde trajecten, met/zonder attachments.
4. **Security**
   - Secret handling (Supabase secrets/KMS), raw MIME naar storage i.p.v. DB.
5. **Output**
   - **`INBOX_DB_CHECK.md`** met velden/relaties/indexes, **SQL-diff**, voorbeeldqueries en **NEXT RESEARCH**.
