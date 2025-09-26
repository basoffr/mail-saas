# Tab 3 — Campagnes (Implementatieplan)

## 0) Doel & scope
- **Doel:** Campagnes opzetten, plannen, monitoren en beheren, met throttling per domein, verzendvensters, dedupe-regels en optionele follow-up (met bijlage).
- **In scope (MVP):**
  - Overzicht & detail van campagnes
  - Wizard (Basis → Doelgroep → Verzendregels → Review)
  - Queueing & scheduling (Europe/Amsterdam, ma–vr 08:00–17:00, 1/20 min per domein)
  - Pauzeren/hervatten/stoppen
  - Follow-up inplannen (X dagen na eerste mail; optionele rapport-bijlage)
  - KPI’s: gepland, verstuurd, opens
- **Niet in scope (MVP):**
  - Click/reply tracking
  - A/B-testing
  - Geavanceerde stopregels (alleen read-only tekst voor nu)

---

## 1) UI-structuur & states
### 1.1 Overzicht
- **Kolommen:** Naam, Status (draft|running|paused|completed), Template, Doelgroep (#leads), Verzonden, Opens %, Startdatum.
- **Acties per rij:** Bekijken (detail), Pauzeren/Hervatten (alleen running/paused), Stoppen (hard stop), Dupliceren.
- **Zoek/Filter:** zoek op naam; filter op status en datum.
- **Lege staat:** CTA “Nieuwe campagne”.

### 1.2 Wizard (4 stappen)
**Stap 1 — Basis**
- Velden: Campagnenaam (text), Template (dropdown), Startmoment (Nu | Gepland datetime).
- Follow-up: Aan/Uit (default Aan), X dagen (default 3), “Bijlage toevoegen indien beschikbaar” (checkbox).

**Stap 2 — Doelgroep**
- Keuzes:
  - **Filter**-modus: UI-filters op Leads (status ≠ suppressed/bounced, TLD, has_image, vars-criteria, datum “last_emailed_at ≥ …”).
  - **Statische selectie**: leads geselecteerd uit Leads-tab (via selectie buffer) of ad-hoc keuze.
- Preview: totaal aantal leads + steekproef (20 items).
- **Dedupe-regels (checkboxen):**
  - Exclude suppressed/bounced (forced on)
  - Exclude already contacted in last **N** dagen (default 14; bewerkbaar)
  - One-per-domain (optioneel)
- Validatie: doelgroep > 0 vereist.

**Stap 3 — Verzendregels**
- Domeinen (checkboxes; read-only lijst uit Instellingen; min. 1 vereist).
- Throttle (read-only in MVP): 1 e-mail / **20** min / **per domein**.
- Venster (read-only in MVP): ma–vr **08:00–17:00** (Europe/Amsterdam).
- Retry policy (read-only tekst): 2 retries met exponential backoff (bij provider/timeouts).
- Stopregels (read-only tekst): “Pauzeer campagne bij te hoge bounce-ratio” (future).

**Stap 4 — Review & Start**
- Samenvatting: naam, template, doelgroep-aantal, domeinen, startmoment, follow-up (instellingen).
- **Dry-run** (optioneel): simuleert planning per dag (“zou plannen: X vandaag, Y morgen…”).
- **Start campagne**: maakt records aan en zet status **running** → redirect naar detail.

### 1.3 Detail
- **Header:** Naam, Status-badge, knoppen (Pauzeren/Hervatten, Stoppen).
- **KPI-tegels:** Gepland (totaal berichten), Verstuurd, Opens (%), Fouten (count), Gem. tempo/h.
- **Grafiek:** Verzonden per dag; secundaire as: opens per dag (optioneel).
- **Tabel Berichten:** Lead email, Domein gebruikt, Gepland, Verzonden, Status (queued|sent|bounced|opened|failed), Laatste event.
  - Acties per bericht: **Resend** (alleen bij failed; guard modal), **Bekijk render** (HTML snapshot).
- **Follow-up panel:** Instellingen (X dagen, bijlage ja/nee), aantallen gepland/verzonden.

- **Statusovergangen:**
  - draft → running (bij start)
  - running ↔ paused (pauzeren/hervatten)
  - running/paused → completed (als alle berichten eindstatus hebben) of **stop** (hard stop: nieuwe sends blokkeren, queue leegmaken)

---

## 2) Data & modellen (conceptueel)
- **campaigns**: `id`, `name`, `template_id`, `start_at`, `status`, `followup_enabled`, `followup_days`, `followup_attach_report`, `created_at`, `updated_at`.
- **campaign_audience**: (materialized of query) snapshot van geselecteerde `lead_id`s (met timestamp), incl. dedupe-keuzes.
- **messages**: per lead één outbound message: `id`, `campaign_id`, `lead_id`, `domain_used`, `scheduled_at`, `sent_at`, `status`, `last_error`, `open_at (nullable)`.
- **message_events** (optioneel in MVP): `message_id`, `type` (sent/open/bounce/failed), `created_at`, `meta`.
- **followup_messages** (kan in `messages` met `parent_message_id`): geplande follow-ups koppelen aan eerste bericht.

---

## 3) Scheduling & queueing (functioneel)
- **Tijdzone:** Europe/Amsterdam.
- **Verzendvenster:** alleen **ma–vr** tussen **08:00–17:00**.
- **Throttle:** 1 bericht per **20 min** **per domein** (dus parallel over domeinen; 4 domeinen = 12/h totaal).
- **Domeinkeuze per bericht:** round-robin of least-recently-used per domein om de 20-minute-sleuf te vullen.
- **Planning:** bij start campagne worden **messages** aangemaakt met `scheduled_at` slots volgens venster + throttle.
  - Als startmoment “nu”: eerstvolgende slot per domein binnen venster.
  - Als slot buiten venster valt (avond/weekend): doorschuiven naar eerstvolgende geldige vensterstart.
- **Pauseren:** geen nieuwe `sent_at`; `scheduled_at` blijft, maar **sender** slaat geplande sends over tot hervatting (of verplaatst naar eerstvolgende geldige slot—kies één en documenteer).
- **Stoppen:** verdere sends blokkeren (zet resterende queued op ‘canceled’ of `status=stopped`).
- **Retries:** bij tijdelijke fouten (timeouts/4xx-soft): plan retry in aparte retry-lanes (respecteer throttle).
- **Follow-up:** bij **sent** van eerste bericht → plan follow-up `scheduled_at = sent_at + X dagen` (ingebed in venster/throttle). Als “bijlage indien beschikbaar”: voeg rapport toe als er één is gekoppeld aan de lead of campagne.

---

## 4) Dedupe & suppressie (functioneel)
- **Suppressie:** leads met `status = suppressed|bounced` worden niet ingepland.
- **Recency dedupe:** exclude leads met `last_emailed_at >= now - N dagen` (default 14).
- **One-per-domain (optioneel):** bij aanzetten: kies slechts één lead per `lead.domain`; rest droppen of naar aparte lijst “uitgesloten (one-per-domain)”.
- **Na send:** update `leads.last_emailed_at` en bij open → `leads.last_open_at`.

---

## 5) API-contracten (zonder code)
- `GET /campaigns` → overzicht met pagination/filters.
- `POST /campaigns` → zie payload in API.md (naam, template_id, audience, schedule, domains, followup).
- `GET /campaigns/{id}` → detail (incl. KPI’s, timeline, messages pagina-gewijs).
- `POST /campaigns/{id}/pause` | `/resume` | `/stop`.
- `POST /campaigns/{id}/dry-run` → simulatie-by-day.
- `GET /messages?campaign_id=...` → berichtentabel (filters op status).
- `POST /messages/{id}/resend` (alleen bij `failed`).
- **Tracking**: `GET /track/open.gif?m=...&t=...` (events loggen).

---

## 6) Validaties & foutafhandeling
- **Wizard Stap 1:** naam verplicht; template gekozen; startmoment valide (≥ nu).
- **Wizard Stap 2:** doelgroep > 0; filters/IDs geldig; dedupe-keuzes toegepast.
- **Wizard Stap 3:** ≥1 domein geselecteerd; throttle & venster read-only bevestigd.
- **Start:** als er geen geldige slots binnen venster zijn (b.v. het is weekend), plan naar eerstvolgende werkdag 08:00.
- **Pauzeren:** running vereist; meerdere klikken idempotent.
- **Stoppen:** bevestigingsmodal (onherroepelijk); queued → ‘canceled’.
- **Resend:** alleen bij `failed`; respecteer venster/throttle; toon waarschuwing bij suppressie.

---

## 7) Performance & schaal
- **Message-creation** in batches (bijv. 500 per chunk) om UI/DB niet te blokkeren.
- **Indices** op `messages(campaign_id, status, scheduled_at)`, `leads(last_emailed_at)`.
- **Lazy loading** voor berichtentabel en timeline.
- **Dry-run** doet geen writes; berekent slots in-memory op basis van venster/throttle.

---

## 8) Beveiliging & privacy
- **Auth verplicht** voor alle campagne-endpoints.
- **Access control**: single-team; geen mixed data.
- **Unsubscribe**: alle uitgaande e-mails bevatten list-unsubscribe (mailto + URL).
- **Data-minimalisatie**: in detailtabel geen volledige body tonen, alleen render preview via secure endpoint.

---

## 9) Telemetrie & logging
- **Events:** `campaign_created`, `campaign_started`, `campaign_paused`, `campaign_resumed`, `campaign_stopped`, `message_scheduled`, `message_sent`, `message_failed`, `message_opened`.
- **Metrics:** sends per uur, opens per uur, failure rate, queue depth (optioneel), slot-utilization per domein.

---

## 10) QA-checklist & acceptatiecriteria
**Overzicht**
- [ ] Lijst toont status, counts en startdatums correct.
- [ ] Zoek/filter werkt (status, naam, datum).

**Wizard**
- [ ] Doelgroepselectie levert correct #leads (na dedupe).
- [ ] Domeinen zijn zichtbaar en selecteerbaar; ≥1 verplicht.
- [ ] Review-samenvatting klopt; start zet campagne op **running**.

**Scheduling**
- [ ] Verzendvenster/Throttle worden gevolgd: max 1/20 min/domain, alleen 08–17h ma–vr.
- [ ] “Nu” start: eerste slots zijn binnen huidige venster; buiten venster -> eerstvolgende dag 08:00.
- [ ] Pauseren stopt verdere sends; hervatten herpakt schema zonder dubbele sends.
- [ ] Stoppen: queued berichten gaan naar canceled; geen nieuwe sends.

**Detail**
- [ ] KPI’s updaten live (verstuurd, opens).
- [ ] Berichtentabel filtert op status; “Resend” alleen bij failed.

**Follow-up**
- [ ] Bij enabled: follow-up wordt gepland op `sent_at + X dagen` binnen venster/throttle.
- [ ] Bijlage wordt toegevoegd indien beschikbaar (lead/campagne-koppeling).

**Tracking**
- [ ] Opens worden gelogd en zichtbaar bij KPI’s.

**Fouten**
- [ ] Tijdelijke SMTP/provider fouten → retry (tot 2x) met backoff.
- [ ] Permanente bounce → markeer als bounced; suppress future (system-wide).

---

## 11) Dependencies & volgorde
1. **SCHEMA.md** uitbreiden met `campaigns`, `messages`, `campaign_audience`, `message_events`.
2. **Endpoints** (create, list, detail, actions, dry-run).
3. **Scheduler/Queue** logic (slots, venster, per-domein throttle, retries).
4. **Detailpagina** met KPI’s, grafiek, berichtentabel.
5. **Follow-up** planning integreren.
6. **Tracking pixel** meenemen in template render flow.
7. **QA** op volledige lifecycle (draft → running ↔ paused → completed/stop).

---

## 12) Definition of Done (Campagnes)
- Campagnes kunnen worden aangemaakt via wizard met duidelijke review.
- Doelgroep wordt correct bepaald (filters of statische selectie) en gededuped.
- Berichten zijn gepland met respect voor venster/throttle en worden verstuurd.
- Pauzeren/hervatten/stoppen werkt voorspelbaar.
- KPI’s en detailtabel geven realtime inzicht; opens worden geteld.
- Follow-ups worden ingepland en verzonden conform instellingen (met optionele bijlage).
