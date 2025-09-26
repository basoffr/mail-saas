# 🌀 Windsurf Superprompt – Tabblad 3 (Campagnes)

Lees eerst zorgvuldig de volgende projectbestanden in:  
- `api.md`  
- `rules.md`  
- `readme.md`  
- `implementationplan.md`  
- `tab3_campagnes_implementatieplan.md`  
- `lovable-prompts.md`  
- `schema.md` (indien aanwezig)  

⚠️ Pas **uitsluitend code aan die relevant is voor Tabblad 3 (Campagnes)**.  
Andere modules (Leads, Templates, Rapporten, Statistieken, Instellingen) mogen **niet** aangepast worden.  

---

## ✅ Opdracht

### 1. Router & Endpoints
- Maak `api/campaigns.py` met endpoints exact volgens **API.md** en **tab3_campagnes_implementatieplan.md**:
  - `GET /campaigns` → lijst met filters en paginatie.  
  - `POST /campaigns` → payload met naam, template_id, audience, schedule, domains, followup.  
  - `GET /campaigns/{id}` → detail met KPI’s, timeline, berichten.  
  - `POST /campaigns/{id}/pause|resume|stop`.  
  - `POST /campaigns/{id}/dry-run` → simulatie van planning per dag.  
  - `GET /messages?campaign_id=...` → berichtenlijst.  
  - `POST /messages/{id}/resend` (alleen bij failed).  
  - Tracking: `GET /track/open.gif?m=...&t=...` → open-event loggen.

- Response-shape uit `rules.md` `{data:..., error:null}`.  
- Auth verplicht via Supabase JWT.  
- Logging events: `campaign_created`, `campaign_started`, `campaign_paused`, `campaign_resumed`, `campaign_stopped`, `message_scheduled`, `message_sent`, `message_failed`, `message_opened`.

---

### 2. Modellen & Schemas
- **Campaigns**: `id`, `name`, `template_id`, `start_at`, `status`, `followup_enabled`, `followup_days`, `followup_attach_report`, `created_at`, `updated_at`.  
- **CampaignAudience**: snapshot van geselecteerde leads (lead_ids + dedupe-keuzes).  
- **Messages**: `id`, `campaign_id`, `lead_id`, `domain_used`, `scheduled_at`, `sent_at`, `status`, `last_error`, `open_at`.  
- **MessageEvents**: optioneel, voor sent/open/bounce/failed.  
- **FollowupMessages**: zelfde tabel of parent-child relatie in messages.  

- Pydantic schemas: `CampaignOut`, `CampaignDetail`, `CampaignCreatePayload`, `MessageOut`.

---

### 3. Services & Worker
- **services/campaign_scheduler.py**:  
  - Respecteer Europe/Amsterdam timezone.  
  - Verzendvenster: ma–vr, 08:00–17:00.  
  - Throttle: 1 bericht / 20 min / domein.  
  - Domeintoewijzing: round-robin of least-recently-used.  
  - Planning: maak messages met `scheduled_at` slots.  
  - Pauseren: stop nieuwe sends, hervatten → herpak schema zonder duplicaten.  
  - Stoppen: queued → `canceled`.  
  - Retry policy: 2 retries met exponential backoff.  
  - Follow-up: plan `sent_at + X dagen` → binnen venster/throttle. Voeg rapport toe indien gekoppeld.

- **services/message_sender.py**:  
  - SMTP stub → status updates in `messages`.  
  - Bounce-detectie → markeer suppressed, update lead.status.  
  - Unsubscribe header altijd aanwezig.  

---

### 4. Validaties & Beveiliging
- Wizard Stap 1: naam verplicht, template gekozen, startmoment ≥ nu.  
- Stap 2: doelgroep > 0, dedupe toepassen.  
- Stap 3: ≥1 domein verplicht, throttle/venster read-only bevestigd.  
- Start: weekend/avond → plan eerstvolgende geldige dag 08:00.  
- Resend alleen bij failed.  
- Auth verplicht (JWT).  
- Geen cross-tenant leaks.  

---

### 5. Tests & Fixtures
- Pytest-tests:  
  - Campaign create met filter/statische selectie.  
  - Dry-run planning → slots correct.  
  - Pauseren/resume/stop → correcte status.  
  - Berichtenstatussen (sent, bounced, opened).  
  - Resend alleen bij failed.  
  - Follow-up geplande berichten met/zonder rapport.  
  - Tracking pixel → open events correct gelogd.  

- Fixtures: leads dataset, templates, campaign payloads.  
- Worker mocked SMTP.  

---

### 6. Definition of Done
- Wizard ondersteunt 4 stappen (Basis, Doelgroep, Verzendregels, Review & Start).  
- Doelgroep wordt correct bepaald en gededuped.  
- Berichten gepland conform venster/throttle.  
- Pauzeren/hervatten/stoppen werken correct.  
- KPI’s en detailpagina updaten realtime.  
- Follow-ups ingepland + verzonden met optionele bijlage.  
- Logging, auth en telemetrie conform rules.md.  
- QA-checklist in `tab3_campagnes_implementatieplan.md` volledig groen.  

---
