# 🌀 Windsurf Superprompt – Tabblad 7 (Inbox/Replies)

Lees eerst zorgvuldig de volgende projectbestanden in:  
- `api.md`  
- `rules.md`  
- `readme.md`  
- `implementationplan.md`  
- `tab7_inbox_replies_implementatieplan.md`  
- `tab6_instellingen_implementatieplan.md` (voor IMAP-accounts sectie)  
- `lovable-prompts.md`  
- `schema.md` (indien aanwezig)  

⚠️ Pas **uitsluitend code aan die relevant is voor Tabblad 7 (Inbox/Replies)**.  
Andere modules (Leads, Templates, Campagnes, Rapporten, Statistieken, Instellingen) alleen wijzigen waar strikt noodzakelijk voor Tab 7 (bv. settings-uitbreiding voor IMAP-accounts).  

---

## ✅ Opdracht

### 1) Routers & Endpoints
Maak nieuwe router `api/inbox.py` en breid `api/settings.py` uit met IMAP-accountbeheer endpoints die het implementatieplan vereisen:

**Inbox** (`api/inbox.py`)
- `POST /inbox/fetch` → start async fetch-job(s) voor alle **actieve** accounts. Response: `{ ok: true, run_id }`.
- `GET /inbox/messages?account_id?&campaign_id?&unread?&q?&from?&to?&page=&page_size=` → lijstweergave met filters en paginatie.
- `POST /inbox/messages/{id}/mark-read` → markeer bericht als gelezen (app-lokaal). Response `{ ok: true }`.
- (Optioneel) `GET /inbox/runs?account_id?&page=&page_size=` → historie per account (start/finish/new_count/error).

**Settings (uitbreiding, `api/settings.py`)**
- `GET /settings/inbox/accounts` → lijst accounts (label, host, port, username masked, active, last_fetch_at, last_seen_uid).
- `POST /settings/inbox/accounts` → create/update (zonder plain password! gebruik `secret_ref`).
- `POST /settings/inbox/accounts/{id}/test` → verbindingscheck IMAP.
- `POST /settings/inbox/accounts/{id}/toggle` → active aan/uit.
- Validatie: minimal interval (server guard) instelbaar via config, default 2 minuten.

Conventies uit `rules.md` gelden overal: response shape `{data:..., error:null}`, auth via Supabase JWT, CORS en logging/metrics.

---

### 2) Modellen & Schemas
**SQLModel-tabellen** (uitbreiden `models/`):
- `MailAccount`:
  - `id (uuid)`, `label`, `imap_host`, `imap_port` (int, default 993), `use_ssl` (bool, default true), `username`, `secret_ref` (string), `active` (bool, default true), `last_fetch_at (ts)`, `last_seen_uid (int)`, `created_at`, `updated_at`.
- `MailMessage`:
  - `id (uuid)`, `account_id (fk)`, `folder` (default 'INBOX')`, `uid (int)`, `message_id (string)`, `in_reply_to (string)`, `references (jsonb string[])`, `from_email`, `from_name`, `to_email`, `subject`, `snippet (text ~20kB)`, `raw_size (int)`, `received_at (ts)`, `is_read (bool)`, `linked_campaign_id (fk, nullable)`, `linked_lead_id (fk, nullable)`, `linked_message_id (fk, nullable)`, `created_at`.
- (Optioneel) `MailFetchRun`:
  - `id (uuid)`, `account_id`, `started_at`, `finished_at`, `new_count`, `error (text)`.

**Uitbreiding outbound `Message`-model**:
- `smtp_message_id (string, unique nullable)`  
- `x_campaign_message_id (uuid nullable)` (eigen header-waarde voor robuuste matching).

**Indices/constraints**:
- Unique op `(account_id, folder, uid)` op `MailMessage`.
- Indices: `message_id`, `in_reply_to`, `received_at`, `from_email`, `linked_campaign_id`, `linked_lead_id`.

**Pydantic schemas** voor responses/payloads:  
- `InboxMessageOut`, `InboxListResponse`, `MarkReadResponse`, `FetchStartResponse`, `MailAccountOut`, `MailAccountUpsert`, `MailAccountTestResponse`, `InboxRunOut`.

---

### 3) Services
Voeg services toe in `services/inbox/`:

- `imap_client.py`  
  - IMAPS connect (SSL: verplicht), LOGIN (gebruik `username` + het via secrets opgehaalde wachtwoord voor `secret_ref`), SELECT `INBOX`.
  - Fetch strategie: `UID > last_seen_uid` (voorkeur). Fallback: `SINCE <last_fetch_at>`.
  - Batch FETCH (bv. 50 UIDs per ronde): ENVELOPE + HEADERS (`Message-ID`, `In-Reply-To`, `References`, `From`, `To`, `Subject`, `Date`) en TEXT (alleen eerste 10–20 kB).
  - Robust decode (charset), normaliseer e-mails (lowercase) en onderwerpen (strip “Re:”, “Fwd:” prefixen, trim whitespace).

- `linker.py` (koppelingslogica)  
  1) `in_reply_to` → match op `messages.smtp_message_id`.  
  2) `references[]` → bevat `messages.smtp_message_id`.  
  3) Fallback: `from_email == leads.email` **en** genormaliseerd `subject` match **en** dichtstbijzijnde chronologie t.o.v. `last_emailed_at`.  
  4) Fallback: alleen `from_email == leads.email` → koppel lead, laat `linked_campaign_id` leeg en markeer `weak_link = true` (badge in UI).

- `fetch_runner.py`  
  - Start per actief account een job (APScheduler).  
  - Rate limit guard: minimaal 2 minuten sinds `last_fetch_at`.  
  - Verwerk batches; insert `MailMessage` met unique guard.  
  - Update `last_seen_uid` en `last_fetch_at`.  
  - Registreer `MailFetchRun` (optioneel).  
  - Emit events: `inbox_fetch_started/succeeded/failed`, `reply_linked`.

- `accounts.py`  
  - CRUD/Toggle/Test voor `MailAccount`.  
  - Test: probeer LOGIN + SELECT INBOX; return `{ok, message}` zonder gevoelige velden te loggen.

---

### 4) Validaties & Beveiliging
- **Auth** verplicht (JWT). RBAC: lezen → teamleden; accounts beheren → beheerders.  
- **Secrets**: wachtwoorden nooit opslaan in plaintext; alleen `secret_ref`. Haal credentials op uit de secret store (Render/Supabase Vault) via configurabele adapter.
- **PII-minimalisatie**: alleen headers + snippet (max ~20 kB). Geen volledige body of bijlagen in MVP.  
- **Logging**: nooit credentials of volledige mailcontent loggen. Max 20 foutregels inline; rest als CSV-downloadbare log.  
- **Rate limiting**: server-side guard voor `/inbox/fetch`; UI knop disablen tijdens run.  
- **Charset/encoding**: best-effort decode; bij mislukking markeer `encoding_issue=true` in record en toon best-effort snippet.

---

### 5) Frontend hooks & states (korte aanwijzingen)
- Voeg een **Inbox** pagina/tab toe met tabelkolommen: Datum, Van, Onderwerp, Campagne, Lead, Status, Account.  
- Toolbar: **Ophalen** (disabled tijdens run), **Markeer als gelezen** (bulk).  
- Filters: `unread`, `account_id`, `campaign_id`, `date_from/date_to`, `q` (prefix zoeker over afzender/onderwerp).  
- Detail drawer: headers, snippet, gelinkte entiteiten; knoppen: “Open in campagne”, “Open lead”.  
- Campagne-detail: paneel **Replies** met dezelfde lijst-API maar vast `campaign_id`.

---

### 6) Tests & Fixtures
**Pytest** (API + services):
- `/inbox/fetch`:  
  - Start run → jobs per actief account, respecteer min-interval guard.  
  - IMAP timeout bij 1 account blokkeert andere accounts niet.  
- Koppeling (`linker`):  
  - Met/zonder `In-Reply-To` en `References`.  
  - Fallbacks op `from_email + subject` + chronologie.  
  - Weak link gemarkeerd als `weak_link=true` (expose in `InboxMessageOut`).  
- Lijstendpoint: filters (unread/account/campaign/date/q), sort op `received_at` desc, paginatie.  
- Mark-read: toggelt `is_read` en is idempotent.  
- Settings-accounts: create/update/test/toggle, geen password-leak, username gemaskeerd in responses.

**Fixtures**:  
- Fake IMAP server/mock (of stub) met samples: headers met/zonder `In-Reply-To`, multi-recipient; verschillende encodings.  
- Sample outbound messages met `smtp_message_id` en gekoppelde leads/campagnes.

Coverage doel: ≥60% voor nieuwe modules.

---

### 7) Definition of Done
- **Ophalen** haalt nieuwe INBOX-mails binnen voor alle actieve accounts en toont ze in de UI.  
- Berichten zijn **automatisch gekoppeld** aan lead/campagne/message waar mogelijk; onzekere koppelingen hebben badge.  
- **Markeer als gelezen** werkt app-lokaal en blijft bewaard in `MailMessage.is_read`.  
- Settings heeft een **IMAP-accounts** sectie met test/toggle en toont fouten duidelijk.  
- Beveiliging, privacy en logging voldoen aan `rules.md`.  
- QA-checklist uit het implementatieplan is groen.

---
