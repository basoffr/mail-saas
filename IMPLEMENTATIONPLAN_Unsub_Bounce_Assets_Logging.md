# ADDENDUM — Unsub/Bounce, Rapport & Afbeeldingen, Handtekening, Logging (definitief)

## 1) Unsubscribe & Bounce → **géén automatische acties**, wél handmatig **Lead Stop**
**Kernbesluit:** we bouwen **geen** automatische afhandeling op events (unsubscribe/bounce). In plaats daarvan een **handmatige “stop lead”** functie.

- **Data**
  - `leads.stopped` (boolean, default `false`).

- **Scheduler-guard (verplicht)**
  - Voor **elke** geplande send: eerst check `if lead.stopped: cancel`.
  - Annuleer alle toekomstige sends voor deze lead: update `send_queue.status = 'canceled'` (alle `queued` items).

- **API**
  - `POST /leads/{lead_id}/stop`
    - Request body: `{}` (leeg).
    - Response (idempotent): `200 {"ok":true,"lead_id":"...","stopped":true,"canceled":<int>}`.
    - Fouten:
      - `404 {"error":"lead_not_found"}`

- **UI**
  - **Lead detail**: knop **“Stop verdere mails naar deze lead”** (met confirm).  
  - **Geen** stopknop op Campagne-detail.

- **Tests**
  - Unit: `stopped=True` → scheduler plant/verstuurt niets voor deze lead.  
  - Integratie: `POST /leads/{id}/stop` → alle toekomstig `queued` items → `canceled`.  
  - E2E: na M2 lead stoppen → M3/M4 gaan **niet** meer uit.

> NB: Unsubscribe/bounce kunnen later worden gekoppeld aan deze stop-actie, maar **nu niet** (bewuste keuze).

---

## 2) Rapportkoppeling (Mail 3) — **per domein vaste bestandsnaam**, permissief
**Kernbesluit:** Mail 3 **mag altijd verstuurd worden**, ook als geen rapportbestand gevonden wordt.

- **Naamconventie (per domein)**
  - **Root-key** per domein (hard-coded mapping), bijv.:
    - `punthelder-marketing.nl` → `running_nl`
    - `punthelder-vindbaarheid.nl` → `cycle_nl`
  - Rapportbestand: `assets/{root}_report.pdf` (bijv. `assets/running_nl_report.pdf`).

- **Gedrag**
  - Bij renderen Mail 3: probeer rapport te attachen via pad hierboven.
  - Niet gevonden → **verzenden zonder attachment** (géén blokkade/geen retry).

- **Logging-flag**
  - In `send_queue`: `with_report` (bool). `true` als attachment is meegestuurd, anders `false`.

- **Tests**
  - Met rapportbestand → `with_report=true`.  
  - Zonder bestand → `with_report=false`, status `sent`.

---

## 3) Dashboard-afbeelding (Mail 1 & 2) — **per domein vaste bestandsnaam**, permissief
**Kernbesluit:** Mail 1/2 **mogen altijd verstuurd worden**, ook als geen afbeelding gevonden wordt.

- **Naamconventie (per domein)**
  - Afbeeldingbestand: `assets/{root}_picture.png` (bijv. `assets/running_nl_picture.png`).

- **Template-placeholder**
  - `{{image.cid 'dashboard'}}` → renderer voegt inline CID toe **alleen** als bestand bestaat; anders leeg.

- **Gedrag**
  - Niet gevonden → **verzenden zonder afbeelding** (géén blokkade/geen retry).

- **Logging-flag**
  - In `send_queue`: `with_image` (bool). `true` als CID is ingesloten, anders `false`.

- **Tests**
  - Met bestand → `with_image=true`.  
  - Zonder bestand → `with_image=false`, status `sent`.

---

## 4) Handtekening / naamvelden — **altijd afbeelding per alias**
**Kernbesluit:** ondertekening **altijd** via afbeelding; bestanden worden door ons aangeleverd en ontbreken niet.

- **Paden (verplicht aanwezig)**
  - Christian: `assets/signatures/christian.png`
  - Victor:    `assets/signatures/victor.png`

- **Renderer**
  - Voeg onderin elke mail `<img src="cid:signature" …>` in op basis van alias (Christian/Victor).
  - **Geen** tekstuele fallback nodig.

- **Tests**
  - Beide signature-bestanden aanwezig → signature-CID ingesloten.

---

## 5) Logging per mail + CSV export (inzicht per lead/alias/domein)
**Kernbesluit:** gedetailleerde logging in DB + downloadbare CSV.

- **send_queue** (uitbreiden met):
  - `with_image`  (boolean, default `false`)
  - `with_report` (boolean, default `false`)

- **CSV export endpoint**
  - `GET /exports/sends.csv`  
  - **Kolomvolgorde (exact):**  
    1) `campaign_id`  
    2) `lead_id`  
    3) `domain`  
    4) `alias`  
    5) `step_no`  
    6) `template_id`  
    7) `scheduled_at`  
    8) `sent_at`  
    9) `status`  
    10) `with_image`  
    11) `with_report`  
    12) `error_code`  
    13) `error_message`

- **UI**
  - Statistieken/Reports: knop **“Download sends-log (CSV)”**.

- **Tests**
  - Integratie: CSV bevat exacte kolommen en correcte waarden per send.

---

## 6) Errors (enkel relevant voor dit addendum)
- `POST /leads/{lead_id}/stop`
  - 200 `{"ok":true,"lead_id":"...","stopped":true,"canceled":<int>}`
  - 404 `{"error":"lead_not_found"}`

> Geen extra foutcodes rond assets: ontbreken van rapport/afbeelding blokkeert **niet** en geeft geen error—alleen flags in logging.

---

### Samenvatting (één alinea voor boven in PR)
- **Geen automatische unsub/bounce.** In plaats daarvan **handmatige stop per lead** (systeem-breed) via `POST /leads/{id}/stop` en een knop op Lead-detail; scheduler cancelt toekomstige sends.  
- **Mail 3 rapport** en **Mail 1/2 afbeelding** worden gezocht op **per-domein vaste bestandsnamen**; ontbreken blokkeert **niet**; verzenden gaat door en we loggen `with_report`/`with_image`.  
- **Handtekening** is **altijd** een image per alias (Christian/Victor).  
- **Per-mail logging** in `send_queue` en **CSV export** via `GET /exports/sends.csv`.

— Einde addendum —
