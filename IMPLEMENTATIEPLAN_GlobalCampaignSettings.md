# 📌 IMPLEMENTATIEPLAN — Global Campaign Settings + Domein-Flows (Hard-coded)

## 0) Doel & Scope
- **Hard-coded** verzendregels en 4-staps campagneflows **per domein** (geen overrides in UI of per campagne).
- **Initial outreach → Christian**; **follow-ups → Victor** (per flow-stap vastgelegd).
- **Settings UI** toont alles **read-only** vanuit backend (geen DB nodig); sluit aan op bestaand `/settings` endpoint.
- Integreert met bestaande MVP-tabs (Leads, Campagnes, Templates, Rapporten, Statistieken, Instellingen).

---

## 1) Architectuur & Conventies
- Frontend: React/Next.js + Tailwind + shadcn/ui (Lovable/Windsurf).
- Backend: FastAPI (Render), Python 3.11+, Supabase later (nu nog niet nodig).
- API-vorm: `{data, error}` en TZ Europe/Amsterdam.

---

## 2) Verzendregels (hard-coded, per domein)
**Geldig voor alle Christian initial-mails (en feitelijk voor elk alias binnen het domein, omdat throttle per domein is):**

- **Throttle-scope:** per **domein** (niet per alias).  
- **Tijdzone:** Europe/Amsterdam.  
- **Werkdagen:** maandag t/m vrijdag.  
- **Feestdagen:** negeren (behandelen als normale werkdag).  
- **Venster (hard):** `[08:00, 17:00)` lokaal.  
- **Slotgrid:** elke 20 minuten → `:00, :20, :40`.  
- **Laatste geplande slot:** **16:40**.  
- **Aantal slots/dag/domein:** 27.  
- **Grace window:** uitloop toegestaan tot **18:00** voor **reeds geplande** slots; wat daarna overblijft → **volgende werkdag 08:00**.  
- **Dagcap:** 27 mails per domein per werkdag.  
- **Queueing & prioriteit:** FIFO per domein.  
- **Cross-domain:** parallel (4 domeinen ⇒ 12/h, 108/dag).  
- **Backlog:** nooit skippen; altijd doorduwen.  
- **Max 1 campagne tegelijk per domein:** nieuwe campagne wordt geweigerd of gequeued als er al één actief is.

---

## 3) 4-staps flows (hard-coded) — versie per domein
**Interval tussen mails:** 3 werkdagen per stap.  
**Alias-rol:** M1/M2 via **christian**, M3/M4 via **victor**.  
**Templates:** per versie **hard-coded** (subject/body + placeholders).

Voorbeeldconfig:
```python
@dataclass(frozen=True)
class Step:
    alias: str
    template_id: str
    delay_days: int

@dataclass(frozen=True)
class Flow:
    version: int
    domain: str
    steps: List[Step]

FLOWS = {
    "punthelder-marketing.nl": Flow(
        version=1, domain="punthelder-marketing.nl",
        steps=[
            Step("christian","v1_mail1",0),
            Step("christian","v1_mail2",3),
            Step("victor","v1_mail3",6),
            Step("victor","v1_mail4",9),
        ],
    ),
    "punthelder-vindbaarheid.nl": Flow(
        version=2, domain="punthelder-vindbaarheid.nl",
        steps=[
            Step("christian","v2_mail1",0),
            Step("christian","v2_mail2",3),
            Step("victor","v2_mail3",6),
            Step("victor","v2_mail4",9),
        ],
    ),
    "punthelder-seo.nl": Flow(
        version=3, domain="punthelder-seo.nl",
        steps=[
            Step("christian","v3_mail1",0),
            Step("christian","v3_mail2",3),
            Step("victor","v3_mail3",6),
            Step("victor","v3_mail4",9),
        ],
    ),
    "punthelder-zoekmachine.nl": Flow(
        version=4, domain="punthelder-zoekmachine.nl",
        steps=[
            Step("christian","v4_mail1",0),
            Step("christian","v4_mail2",3),
            Step("victor","v4_mail3",6),
            Step("victor","v4_mail4",9),
        ],
    ),
}
```

---

## 4) Scheduler & Sender (gedrag)
- **Mail 1 timing:** niet direct, maar altijd in het eerstvolgende slot.  
- **Intervals:** altijd +3 **werkdagen** (weekend overslaan).  
- **Slotgeneratie per domein per werkdag:** 27 timestamps (08:00..16:40, elke 20m) in Europe/Amsterdam; intern in UTC plannen.  
- **Throttle per domein:** 1 send per slot; FIFO binnen domein.  
- **Grace window:** uitvoering mag uitlopen tot 18:00 voor reeds ingeplande slots.  
- **Backlog:** overschot na 18:00 → volgende werkdag 08:00.  
- **Cross-domain:** parallellisatie per domeinrij; 4 domeinen ⇒ 12/h, 108/dag (max).  
- **Flow-timing:** bij campagnes op domein X genereert de backend M1 (dag 0), M2 (+3 wd), M3 (+6 wd), M4 (+9 wd); elke stap via `next_valid_slot`.

---

## 5) API-uitbreidingen (read-only)
### `GET /settings` (read-only)
- Levert **sending policy** + **domain/alias-overzicht** + **flow-versie per domein**.  
- `POST /settings` blijft uitgeschakeld voor deze velden.

Voorbeeldresponse:
```json
{
  "data": {
    "sending": {
      "timezone":"Europe/Amsterdam",
      "days":["Mon","Tue","Wed","Thu","Fri"],
      "window":{"from":"08:00","to":"17:00","inclusiveEnd":false},
      "grace_to":"18:00",
      "throttle":{"scope":"per_domain","minutes":20},
      "daily_cap_per_domain":27
    },
    "domains":[
      {"domain":"punthelder-marketing.nl",
       "aliases":[
         {"email":"christian@punthelder-marketing.nl","role":"initial"},
         {"email":"victor@punthelder-marketing.nl","role":"followup"}],
       "flow_version":1
      }
    ],
    "notes":["Values are hard-coded in backend"]
  },
  "error": null
}
```

---

## 6) Frontend taken
### Instellingen (Tab 6) — read-only
- Card “Verzendregels”: TZ, dagen, venster `[08:00–17:00)`, grace tot 18:00, throttle “1/20m per domein”, dagcap 27.  
- Card “Domeinen & Aliassen”: tabel per domein + badges voor christian/victor + “Flow-versie v1–v4”.  
- Optioneel mini-flowpreview per domein: “M1/M2 via Christian, M3/M4 via Victor; 3 werkdagen interval”.

### Campagnes (Tab 3)
- Wizard stap 3 “Verzendregels”: alleen samenvatting (read-only).  
- Wizard logica: backend bindt de flow van het gekozen domein (v1–v4) en plaatst 4 messages in queue (0/+3/+6/+9 werkdagen).  
- Detailpagina: geen overrides, alleen flow preview.

### Templates (Tab 2)
- Toon de 4 versies met hun 4 mails (16 templates) read-only; preview/testsend.

---

## 7) Stats & Rapportage
- **Dagtoekenning:** uitloop tot 18:00 telt als dag X (niet dag X+1).  
- **Flow completion:** rapporteren hoeveel leads M1→M4 hebben doorlopen, vs. gebounced/unsubscribed.  

---

## 8) Alias/identiteit
- **Initial → Christian**, **follow-ups → Victor** (hard-coded).  
- **From/Reply-To:**  
  - Follow-ups via Victor versturen met `From: Victor`, maar `Reply-To: Christian`.  
  - Ontvangers zien “From: Victor”; antwoorden landen bij Christian.  
- **Handtekening:** later via afbeelding/templating.

---

## 9) Open items (bewust later)
- Unsubscribe-gedrag (na M2 unsub → M3/M4 annuleren?).  
- Bounce-gedrag (na M1 hard bounce → rest stoppen?).  
- Rapportkoppeling (Mail 3): per-lead binding vs. generiek.  
- Dashboard-afbeelding per lead vs. generiek + fallback/warnings.  
- Handtekening/naamvelden via afbeelding/templating.

---

## 10) Testplan
**Unit (backend):**
- Slotgenerator: 27 slots per werkdag; laatste 16:40; grace tot 18:00.
- FIFO en domein-throttle werken correct.
- Flow mapping: domein → versie → alias/template per stap.

**Integratie:**
- `GET /settings` levert hard-coded waarden.
- Campaign create → 4 geplande messages op correcte dagen/slots.

**E2E:**
- Campagne op vrijdag start om 16:50 → M1 verplaatst naar maandag 08:00.
- Scenario’s vlak voor 17:00 → uitloop tot 18:00 werkt.
- Cross-domain: 12/h, 108/dag maximaal.

---

## 11) Acceptatiecriteria
- Instellingen-pagina toont exact de hard-coded policy + domein/alias + flow-versie read-only.  
- Campagne-wizard genereert per domein de juiste flow (v1–v4, alias + 3 werkdagen intervals).  
- Sender/Scheduler respecteert venster, slots, throttle, grace, FIFO, dagcap, en max 1 campagne/domein.  
- Templates van alle versies renderen correct (placeholders & CID-afbeelding).  
- Stats tonen correcte dagindeling en flow completion.

---

# 🔒 Guardrails (Niet-onderhandelbaar)

- GEEN overrides in UI of per campagne of alias. Elk PR dat dit toevoegt = reject.
- /settings: alleen GET. POST/PUT/PATCH voor sending policy/flows = 405 of `{error:"hard-coded"}`.
- Domein-throttle is heilig: 1/20m PER DOMEIN, slotgrid :00/:20/:40, [08:00,17:00), laatste slot 16:40, dagcap 27, grace tot 18:00.
- Max 1 campagne ACTIEF per domein. Nieuwe campagne op dat domein ⇒ 409 "domain busy".
- Intervals zijn +3 WERKDAGEN. Weekend = geen slots. Alles buiten venster/weekend ⇒ push naar eerstvolgend geldig slot (meestal ma 08:00).
- Backlog wordt NOOIT geskipt; altijd doorrollen tot dagcap en dan naar volgende werkdag 08:00.
- Alias-rollen staan vast per flow: M1+M2=christian, M3+M4=victor. From/Reply-To voor follow-ups: From=Victor, Reply-To=Christian.
- Templates zijn hard-coded per versie/mail. Geen dynamische aanpassing buiten placeholders.
- Open items (unsub/bounce, rapport/afbeeldingen, handtekening) zijn PENDING → NIET implementeren zonder expliciete nieuwe opdracht.
