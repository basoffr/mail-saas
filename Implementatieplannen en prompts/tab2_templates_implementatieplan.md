# Tab 2 — Templates (Implementatieplan)

## 0) Doel & scope
- **Doel:** Templates beheren die variabelen (lead.*, vars.*, campaign.*) en per-lead afbeeldingen ondersteunen, met **preview** (server-side render) en **testsend**.
- **In scope (MVP):**
  - Lijst & detailweergave (hard-coded templates uit backend zichtbaar in UI).
  - Variabelenoverzicht (automatisch afgeleid).
  - Server-side **Preview** met gekozen test-lead.
  - **Testsend** naar willekeurig adres, gerenderd met een gekozen lead.
- **Niet in scope (MVP):**
  - WYSIWYG editor of runtime bewerken (templates zijn read-only).
  - Versiebeheer / AB-testing.

---

## 1) UI-structuur & states
### 1.1 Lijst
- **Kolommen:** Naam, Onderwerp, Laatst gewijzigd (seed timestamp), Aantal vereiste variabelen (badge), Status (read-only).
- **Acties per rij:** **Preview**, **Variabelen**, **Testsend**, **Bekijken**.
- **Zoek/Filter:** zoek op naam/onderwerp; filter op “heeft afbeeldingenlot(s)”, “heeft ontbrekende vars bij sample lead” (optioneel).

### 1.2 Detail (read-only)
- **Secties:**
  - **Meta:** Naam, Onderwerp (met variabelen), Template-ID.
  - **Body (read-only):** HTML/MJML bron of renderbare template-tekst (monospace view met line numbers).
  - **Variabelenschema (auto):**
    - Lijst: `lead.email`, `lead.company`, `vars.seo_score`, `campaign.name`, `image.cid 'hero'`, etc.
    - Type-hint waar mogelijk (string/number/bool).
  - **Afbeeldingsslots:**
    - Voorbeeld: `hero`, `logo`. Toon of slot **per-lead** is (`image.cid`) of **statisch** (`image.url`).
  - **Validatiewaarschuwingen:** ontbrekende vereiste variabelen voor gekozen voorbeeld-lead (selecteerbaar).

### 1.3 Preview
- **Inputs:** kies **Test lead** (zoeken op email/bedrijf), kies **Template** (indien niet vanuit lijst).
- **Output:** 
  - Gerenderde **HTML** (iframe/modal) en **plain-text** fallback.
  - **Warnings:** missende variabelen/afbeelding(en), lege placeholders, ongeldige e-mail-opmaak in onderwerp.
- **Acties:** “Kopieer HTML”, “Download HTML” (optioneel), “Open als e-mailvoorbeeld” (safe viewer).

### 1.4 Testsend
- **Inputs:** 
  - **To** (e-mail verplicht)
  - **Lead** (selecteer lead voor variabeleinvulling)
- **Actie:** **Verstuur testsend** (hoogste prioriteit in queue).
- **Feedback:** status (queued/sent/failed) + foutmelding bij SMTP/providertest.

---

## 2) Datavelden & normalisatie
- **Template kernvelden (read-only):**
  - `id (uuid)`, `name`, `subject_template`, `body_template`, `updated_at`, `required_vars[]` (afgeleid).
- **Variabelencontext bij render:**
  - `lead.*` (van gekozen lead)
  - `vars.*` (json van lead)
  - `campaign.*` (optioneel; voor previews kan “dummy campaign” gebruikt worden)
- **Afbeeldingsslots:**
  - **Per-lead**: `image.cid '<slot>'` → resolve via lead.image_key of mapping “slot→key”.
  - **Statisch**: `image.url '<key>'` → vaste asset-URL.

---

## 3) Rendering & helpers (contract)
- **Templating engine (MVP-niveau features):**
  - Interpolatie: `{{ ... }}` (paths: `lead.company`, `vars.score`).
  - Conditionals: `{{#if ...}}...{{/if}}`.
  - Helpers:
    - `{{default x 'fallback'}}`
    - `{{uppercase x}}`, `{{lowercase x}}`
  - **Afbeeldingen:**
    - `{{image.cid 'hero'}}` → backend levert CID inline (voor multipart/inline e-mail) of fallback URL voor preview.
    - `{{image.url 'logo'}}` → absolute URL naar storage/CDN.
- **Validatie bij render:**
  - Verzamelen van missende paths (bv. `vars.seo_score` ontbreekt bij lead).
  - Lege strings die “vereist” zijn → waarschuwing.

---

## 4) API-contracten (zonder code, referenties)
- `GET /templates` → lijst (meta + minimal schema).
- `GET /templates/{id}` → detail (subject/body, slots, required_vars[]).
- `GET /templates/{id}/preview?lead_id=...` → `{html, text, warnings[]}`.
- `POST /templates/{id}/testsend` → `{to, lead_id}` → `{ok, error?}`.
- (Optioneel) `POST /previews/render` (template_id + lead_id) generiek gebruikt door UI.

---

## 5) Validaties & foutafhandeling
- **Preview:**
  - Lead moet bestaan en status ≠ suppressed/bounced (toon waarschuwing indien wel).
  - Als per-lead afbeelding ontbreekt voor vereist slot → waarschuwing + placeholder.
  - Onderwerp na render niet leeg; max lengte (bijv. 255 chars).
- **Testsend:**
  - `to` e-mail syntactisch valide (regex).
  - SMTP/provider fout → toon mensvriendelijke melding + log het ruwe error-type.
  - Unsubscribe header **altijd** toevoegen (MVP-standaardtekst).
- **Rate-limit testsend:** bijv. 5/min per gebruiker.

---

## 6) Performance & schaal
- **Preview render** is CPU-licht; cache resultaat voor (template_id, lead_id) 60s (optioneel).
- **Statische assets** via signed URLs; minimaliseer backend-roundtrips.
- **Testsend** in queue met hoge prioriteit, maar respecteer provider-limieten (eigen kanaal “tests”).

---

## 7) Beveiliging & privacy
- **Auth vereist** voor alle endpoints.
- **Access control:** alleen ingelogde teamleden; geen multi-tenant in MVP (maar ontwerp geen cross-org leaks).
- **Output-sanitization:** HTML preview alleen van eigen template; XSS-veilige viewer (no script execution).
- **Logging**: nooit volledige e-mailbody in logs; alleen hash/IDs + status.

---

## 8) Telemetrie & logging
- **Events:** `template_preview_requested`, `template_preview_warned`, `template_testsend_requested`, `template_testsend_sent`, `template_testsend_failed`.
- **Metrics:** previews per minuut, testsend success rate, warnings per template.

---

## 9) QA-checklist & acceptatiecriteria
**Lijst**
- [ ] Templates worden geladen met juiste meta (naam, onderwerp, updated_at).
- [ ] Zoeken op naam/onderwerp werkt.

**Detail**
- [ ] Variabelenschema toont alle gedetecteerde paths (lead.*, vars.*, campaign.*).
- [ ] Afbeeldingsslots (cid/url) worden juist onderscheiden.

**Preview**
- [ ] Render met gekozen lead levert HTML + text.
- [ ] Warnings tonen bij ontbrekende variabelen/per-lead afbeelding.
- [ ] Onderwerp gerenderd en niet leeg.

**Testsend**
- [ ] Valide “to” vereist; ongeldige e-mail → nette fout.
- [ ] Testsend komt aan (handmatige smoke-test).
- [ ] Unsubscribe header aanwezig.

**Beveiliging**
- [ ] Alleen geauthenticeerde users; 401 bij ontbreken token.
- [ ] Geen leakage van andere templates/organisaties.

**Performance**
- [ ] Preview onder 400ms voor veelvoorkomende cases.
- [ ] Testsend queue’t binnen 100ms; status terug na API-call.

---

## 10) Dependencies & volgorde
1. **SCHEMA.md:** `templates` (seed), `assets` (statische assets).
2. **Parser/engine** met helpers + image resolvers (contract zoals hierboven).
3. **Endpoints** (GET list/detail, preview, testsend).
4. **Frontend** lijst/detail + preview modal + testsend form.
5. **QA** op warnings/edge cases (ontbrekende vars/afbeeldingen).

---

## 11) Definition of Done (Templates)
- Templates zichtbaar in UI met meta, variabelenschema en slots.
- Preview rendert HTML + text voor een gekozen lead, met duidelijke warnings indien data ontbreekt.
- Testsend verstuurt e-mail naar opgegeven adres met gerenderde content (unsubscribe header aanwezig).
- Logging/telemetrie aanwezig; auth & privacy geborgd.
