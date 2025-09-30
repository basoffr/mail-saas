# 📌 Prompts voor Windsurf — Global Campaign Settings Implementatie

Deze 5 prompts dekken samen het volledige `IMPLEMENTATIEPLAN_GlobalCampaignSettings.md`.  
Alle regels zijn concreet, zonder ruimte voor eigen invulling.  

---

## Prompt 1 — Backend Policy & Guards

📌 OPDRACHT: Backend Sending Policy + Guards

Gebruik `IMPLEMENTATIEPLAN_GlobalCampaignSettings.md` als bron.  
ALLE regels zijn hard-coded en read-only. Geen eigen invulling.

1. Maak in `app/core/sending_policy.py` een dataclass `SendingPolicy` met velden:
   - timezone="Europe/Amsterdam"
   - days=["Mon","Tue","Wed","Thu","Fri"]
   - window_from="08:00"
   - window_to="17:00" (exclusief → laatste slot 16:40)
   - grace_to="18:00" (uitloop)
   - slot_every_minutes=20
   - daily_cap_per_domain=27
   - throttle_scope="per_domain"

2. Zorg dat alle logica dit beleid gebruikt:
   - 27 slots per werkdag, grid :00/:20/:40
   - laatste geplande slot = 16:40
   - grace tot 18:00
   - dagcap 27/domein/dag
   - throttle 1/20m per domein
   - overschot → volgende werkdag 08:00

3. Pas `/settings` endpoint aan:
   - Alleen GET → geeft dit beleid terug + domeinen/aliassen/flow-versie.
   - POST/PUT/PATCH op sending policy → altijd 405 of `{error:"hard-coded"}`.

4. Voeg API guards toe:
   - `CampaignCreate` met override-velden (throttle, window, tz, etc.) → 400 error.
   - Max 1 actieve campagne per domein: nieuwe campagne voor busy domein → 409 "domain busy".

5. Schrijf unittests:
   - Slotgenerator → exact 27 slots, laatste 16:40, grace tot 18:00.
   - 400 bij CampaignCreate met override.
   - 409 bij tweede campagne voor hetzelfde domein.

---

## Prompt 2 — Backend Flows & Templates

📌 OPDRACHT: Domein-Flows + Templates

Gebruik `IMPLEMENTATIEPLAN_GlobalCampaignSettings.md` als bron.  
Flows en templates zijn hard-coded. Geen eigen invulling.

1. Maak `app/core/campaign_flows.py`:
   - Per domein een Flow object met version, domain, steps.
   - 4 domeinen:
     - punthelder-marketing.nl → versie 1
     - punthelder-vindbaarheid.nl → versie 2
     - punthelder-seo.nl → versie 3
     - punthelder-zoekmachine.nl → versie 4
   - Steps: 
     - Mail 1: christian, dag 0
     - Mail 2: christian, dag +3 werkdagen
     - Mail 3: victor, dag +6 werkdagen
     - Mail 4: victor, dag +9 werkdagen

2. Maak `app/core/templates_store.py`:
   - Alle templates uit het aangeleverde .docx-bestand opnemen.
   - Template_id’s: v1_mail1..v1_mail4, v2_mail1.., v3_mail1.., v4_mail1..v4_mail4.
   - Subject en body exact hard-coded, met placeholders:
     - {{lead.company}}, {{lead.url}}, {{vars.keyword}}, {{vars.google_rank}}
     - inline CID-afbeelding: {{image.cid 'dashboard'}}

3. API:
   - `/templates` en `/templates/{id}` leveren deze hard-coded templates.
   - Alleen GET, geen bewerken.

4. Tests:
   - Flow mapping per domein klopt (alias, versie, interval).
   - Templates renderen placeholders.

---

## Prompt 3 — Scheduler & Sender

📌 OPDRACHT: Scheduler + Sender

Gebruik `IMPLEMENTATIEPLAN_GlobalCampaignSettings.md` als bron.  
Alle timingregels en alias-rollen zijn vast. Geen eigen invulling.

1. Scheduler:
   - Genereer slots per domein per werkdag:
     - start 08:00, laatste 16:40
     - elke 20 minuten
     - 27 slots totaal
   - Overslaan weekenddagen (za/zo).
   - Mail 1 → eerstvolgende geldige slot.
   - Mail 2/3/4 → +3/+6/+9 werkdagen, daarna `next_valid_slot`.

2. Grace window:
   - Uitvoering van ingeplande slots mag uitlopen tot 18:00.
   - Na 18:00 → verplaats rest naar volgende werkdag 08:00.

3. Queueing:
   - FIFO per domein.
   - 1 send per slot per domein.
   - Cross-domain parallel.
   - Max 1 actieve campagne per domein.

4. Alias-rollen:
   - Mail 1 & 2 → versturen met alias Christian.
   - Mail 3 & 4 → versturen met alias Victor.
   - Follow-ups (Victor) → From=Victor, Reply-To=Christian.

5. Tests:
   - Campagne start vrijdag 16:50 → Mail 1 schuift naar maandag 08:00.
   - Campagne start donderdag → Mail 2 komt dinsdag (3 werkdagen).
   - Overschot na 18:00 → volgende werkdag 08:00.

---

## Prompt 4 — Frontend (Settings, Campaigns, Templates)

📌 OPDRACHT: Frontend UI (Settings, Campaigns, Templates)

Gebruik `IMPLEMENTATIEPLAN_GlobalCampaignSettings.md` als bron.  
UI is read-only voor sending policy. Geen overrides.

1. Tab Instellingen (/settings):
   - Card Verzendregels: toon timezone, dagen, venster [08:00–17:00), grace tot 18:00, throttle 1/20m per domein, dagcap 27.
   - Card Domeinen & Aliassen: tabel per domein, aliases (badge christian/victor), flow-versie.
   - Tooltip: “Deze waarden zijn hard-coded in de backend.”
   - Optioneel mini-flowpreview: “M1/M2 via Christian, M3/M4 via Victor; 3 werkdagen interval.”
   - unsubscribe_text en tracking_pixel_enabled mogen wél bewerkbaar blijven.

2. Tab Campagnes:
   - Wizard stap 3: toon alleen samenvatting van globale regels (read-only).
   - Geen override opties.
   - Bij campagne-create: backend koppelt automatisch juiste flow.

3. Tab Templates:
   - Toon alle 16 templates (v1–v4 × 4).
   - Alleen view/preview/testsend.
   - Geen edit.

4. Tests:
   - Settings UI toont hard-coded regels correct.
   - Wizard stap 3 toont alleen samenvatting, geen edit.
   - Templates-tab toont alle 16 versies.

---

## Prompt 5 — Tests & Acceptatie

📌 OPDRACHT: Tests & Acceptatiecriteria

Gebruik `IMPLEMENTATIEPLAN_GlobalCampaignSettings.md` als bron.  
Dek ALLE regels af. Geen eigen interpretatie.

1. Unit-tests backend:
   - Slotgenerator: 27 slots, laatste 16:40, grace ≤18:00.
   - next_valid_slot: weekend skippen, 3 werkdagen interval.
   - API guards: POST /settings → 405, CampaignCreate override → 400, tweede campagne zelfde domein → 409.

2. Integratietests:
   - GET /settings → exacte policy en flows per domein.
   - Campaign create per domein → 4 geplande mails met juiste alias/timing.
   - Templates → juiste subject/body teruggeven.

3. E2E-tests:
   - Campagne vrijdag 16:50 → M1 maandag 08:00.
   - Campagne donderdag → M2 dinsdag (3 werkdagen).
   - Overschot → volgende werkdag 08:00.
   - Flow completion → stats tonen hoeveel leads M1–M4 doorlopen hebben.

4. Acceptatiecriteria:
   - Instellingen-pagina toont exacte policy en flows read-only.
   - Campagne-wizard genereert per domein juiste flow (geen overrides).
   - Scheduler/Sender respecteert venster, grid, throttle, grace, dagcap, max 1 campagne per domein.
   - Templates renderen placeholders correct.
   - Stats rapporteren dagindeling en flow completion.
