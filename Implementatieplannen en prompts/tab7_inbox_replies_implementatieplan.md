# Tab 7 — Inbox/Replies (Implementatieplan)

## 0) Doel & scope
- **Doel:** Inkomende e‑mails (replies) van de gebruikte verzenddomeinen ophalen via **IMAP** en koppelen aan bestaande leads/campagnes/berichten, met een simpele **Ophalen**-actie in de UI.
- **In scope (MVP):**
  - Ophalen via **IMAP (SSL/993)** voor 1..N accounts (per gebruikt domein/mailbox)
  - Alleen map **INBOX**; alleen **nieuwe/ongelezen** sinds laatste fetch
  - Opslaan van **headers + snippet** (eerste 10–20 kB), body volledig optioneel
  - **Koppeling** aan uitgaande berichten via `In-Reply-To` / `References`; fallback op `From + Subject`
  - Lijstweergave, filters, markeer als gelezen (app-lokaal)
- **Niet in scope (MVP):**
  - POP3, mappenbeheer, labels, bidirectionele sync
  - Bijlagen-parsing en full-body opslag (alleen snippet)
  - Full‑text search
  - Automatische sentiment/intent-detectie

---

## 1) UI-structuur & states
### 1.1 Optie A: Tabblad **Inbox**
- **Kolommen:** Datum (received_at), Van (name/email), Onderwerp, Campagne (indien gelinkt), Lead (indien gelinkt), Status (nieuw/gelezen), Account (mailbox label)
- **Acties (toolbar):** **Ophalen** (triggt fetch-job), **Markeer als gelezen** (bulk), Filter/Zoek
- **Filters:** Ongelezen, Per account, Per campagne, Datumrange
- **Zoek:** vrije tekst over afzender/onderwerp (prefix filter, geen full‑text)
- **Detail (drawer/modal):** headers, snippet/body (max ~20 kB), koppelingen (campagne/lead/message), “Open in campagne”
- **Lege staat:** uitleg + knop **Account configureren** (link naar Instellingen)

### 1.2 Optie B: Replies-paneel in **Campagne-detail**
- Paneel “Replies”: subset op basis van `campaign_id`
- Zelfde kolommen/acties als in Inbox, zonder accountfilter
- Ook hier de **Ophalen**‑knop zichtbaar

---

## 2) Instellingen
**Instellingen → E‑mail infrastructuur** uitbreiden met een sectie **Inbox (IMAP)**:
- Tabel **Accounts** (1..N rijen): Label, Host, Port (993), SSL (fixed aan), Username, **Secret ref** (wachtwoord), Laatste fetch, Laatste UID
- Acties: **Account testen** (verbindingstest), **In-/uitschakelen** (toggle “Active”)
- Systeeminstelling: **Minimale interval** tussen handmatige fetches (bijv. 2 min)

> **Veiligheid:** Credentials niet in plain opslaan; gebruik secret storage (Render Secret / Supabase Vault).

---

## 3) Data & modellen (conceptueel)
- **mail_accounts**
  - `id (uuid)`, `label`, `imap_host`, `imap_port` (int, default 993), `use_ssl` (bool, default true), `username`, `secret_ref` (string), `active` (bool), `last_fetch_at (ts)`, `last_seen_uid (int)`, `created_at`, `updated_at`

- **mail_messages**
  - `id (uuid)`, `account_id (fk)`, `folder` (string, default 'INBOX')`, `uid (int)`, `message_id (string)`, `in_reply_to (string)`, `references (string[])`, `from_email`, `from_name`, `to_email`, `subject`, `snippet` (text, max ~20 kB), `raw_size (int)`, `received_at (ts)`, `is_read (bool, app‑lokaal)`, `linked_campaign_id (fk, nullable)`, `linked_lead_id (fk, nullable)`, `linked_message_id (fk, nullable)`, `created_at`

- **uitbreiding messages (outbound)**
  - `smtp_message_id (string, unique nullable)` – Message‑ID van uitgaande mail
  - `x_campaign_message_id (uuid)` – eigen header voor robuuste matching

- **mail_fetch_runs** (optioneel)
  - `id`, `account_id`, `started_at`, `finished_at`, `new_count`, `error (text)`

**Indices & constraints (MVP):**
- Unique op `(account_id, folder, uid)` in `mail_messages`
- Index op `message_id`, `in_reply_to`, `received_at`, `from_email`, `linked_campaign_id`, `linked_lead_id`

---

## 4) Koppelingslogica (replies ↔ campagnes/leads)
**Primair:**
1) `in_reply_to` → match op `messages.smtp_message_id`  
2) `references` → bevat `messages.smtp_message_id` (scan array)

**Fallbacks:**
3) `from_email == leads.email` **en** onderwerp‑match (subject zonder “Re:”, “Fwd:”; whitespace normalisatie) **en** dichtstbijzijnde chronologie t.o.v. laatst verzonden naar deze lead
4) Alleen `from_email == leads.email` → koppel lead, laat `linked_campaign_id` leeg (toon waarschuwing “niet uniek”)

**Resultaat:**
- Stel velden `linked_message_id`, `linked_campaign_id`, `linked_lead_id` waar van toepassing
- Update reply‑rate statistieken buiten Inbox (Stats kan reply‑rate opnemen in future)

---

## 5) Ophalen‑flow (Ophalen‑knop)
1. UI → `POST /inbox/fetch` → start async job (per **actief** account)
2. Job per account:
   - IMAPS connect, SELECT `INBOX`
   - Zoek nieuwe berichten **op basis van UID** (`UID > last_seen_uid`) of **SINCE** (fallback op datum)
   - Voor elke nieuwe UID: FETCH ENVELOPE + HEADERS (`Message‑ID, In‑Reply‑To, References, From, To, Subject, Date`) + TEXT (eerste 10–20 kB)
   - Parse + normaliseer (lowercase e‑mails, strip “Re:” etc.)
   - **Koppelen** volgens §4
   - Insert in `mail_messages`
   - Houd `max(uid)` bij → set `last_seen_uid`
3. Update `last_fetch_at`; registreer **run** (optioneel)
4. UI toont “X nieuwe berichten” toast en refresht lijst

**Rate‑limiting:**
- Server‑side guard: min. interval 2 minuten per account (configurable)
- UI disable “Ophalen” knop tijdens lopende run

---

## 6) API‑contracten (zonder code)
- `POST /inbox/fetch` → start job; response `{ ok: true, run_id }`
- `GET /inbox/messages?account_id?&campaign_id?&unread?&q?&from?&to?&page=&page_size=` → lijst
- `POST /inbox/messages/{id}/mark-read` → `{ ok: true }`
- (Optioneel) `GET /inbox/runs?account_id` → historie met counts/errors
- (Optioneel) `POST /inbox/test-account` → verbindingscheck voor IMAP‑instellingen

**Beveiliging:** alle endpoints auth + basic RBAC (alle teamleden lezen; instellingen wijzigen beperkt).

---

## 7) Validaties & randgevallen
- IMAP login/timeout → nette fout + log; job gaat verder met andere accounts
- Dubbele UIDs → genegeerd door unique‑constraint
- Grote mails → alleen snippet opgeslagen; body volledig niet nodig in MVP
- Multi‑recipient replies → koppel op Message‑ID/headers, niet op To alleen
- Afzender wijzigt adres → fallback subject‑match; markeer als “zwakke koppeling” (badge)
- Onleesbare charset → probeer decode, anders markeer “encoding‑issue” (toon best effort)
- Onjuist geconfigureerde account (wrong host/port) → duidelijke error in runs + Instellingen badge “fout”

---

## 8) Performance & schaal
- IMAP FETCH per batch (bijv. 50 UIDs tegelijk) om round‑trips te beperken
- Alleen headers + snippet → kleine payloads
- Indexen op `received_at` en `account_id` voor snelle lijstweergave
- Paginatie server‑side (25 per pagina)
- “Ophalen” normaal gesproken < enkele seconden bij weinig nieuwe berichten

---

## 9) Beveiliging & privacy
- **IMAPS (993)** verplicht; geen plaintext
- Credentials via **secret store**; nooit loggen
- PII minimalisatie: alleen noodzakelijke headers + snippet
- Toegang tot Inbox alleen voor geauthenticeerde teamleden
- Audit: wie heeft **Ophalen** uitgevoerd (user_id, timestamp)

---

## 10) Telemetrie & logging
- Events: `inbox_fetch_started`, `inbox_fetch_succeeded`, `inbox_fetch_failed`, `reply_linked`
- Metrics: nieuwe berichten per run, link‑ratio (gelinkt vs. onbepaald), gemiddelde looptijd
- Logs: per run eerst 20 fouten (rest als downloadbare CSV)

---

## 11) QA‑checklist & acceptatiecriteria
**Fetch**
- [ ] `POST /inbox/fetch` start job en haalt nieuwe berichten per actief account binnen
- [ ] Min. interval guard werkt; tweede klik binnen interval wordt genegeerd met melding
- [ ] Lijst toont nieuwe items met juiste `received_at` sortering

**Koppeling**
- [ ] Replies met `In‑Reply‑To` matchen op uitgaand `smtp_message_id`
- [ ] Zonder headers → fallback op `from_email + subject` (na normalisatie) werkt in meeste gevallen
- [ ] Onzekere koppelingen tonen badge en ontbreken van `campaign_id` wordt duidelijk

**UI**
- [ ] Filters en zoek werken (unread/account/campaign/datum)
- [ ] Markeer als gelezen (app‑lokaal) toggle werkt

**Robuustheid**
- [ ] Fout in één account blokkeert andere accounts niet
- [ ] Duplicate UID wordt genegeerd (geen dubbele rijen)

**Beveiliging**
- [ ] Alleen geauthenticeerde gebruikers
- [ ] Passwords nooit zichtbaar in UI/logs

---

## 12) Dependencies & volgorde
1. **SCHEMA.md** uitbreiden met `mail_accounts`, `mail_messages`, (optioneel) `mail_fetch_runs` + extra velden op `messages` (outbound IDs)
2. **Instellingen‑UI** voor accounts & toggles, verbindingstest endpoint
3. **Fetch endpoint** + IMAP client + linklogica
4. **Inbox‑UI** (tabblad of campagne‑paneel) + filters + detail
5. **QA** volgens checklist (incl. E2E test op één Vimexx account)

---

## 13) Definition of Done (Inbox/Replies)
- Een klik op **Ophalen** haalt nieuwe INBOX‑mails op voor alle actieve accounts
- Berichten worden getoond met afzender/onderwerp/datum/snippet
- Waar mogelijk zijn berichten automatisch gekoppeld aan lead/campagne/message
- Onzekere koppelingen worden duidelijk gemarkeerd
- Markeer‑als‑gelezen werkt applicatie‑lokaal
- Security/telemetrie aanwezig; credentials veilig beheerd
