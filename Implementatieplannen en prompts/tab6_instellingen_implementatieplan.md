# Tab 6 — Instellingen (Implementatieplan)

## 0) Doel & scope
- **Doel:** Centraal configuratiepunt voor verzendregels, domeinen en unsubscribe/tracking instellingen.  
- **In scope (MVP):**
  - Overzicht van systeeminstellingen (vensters, throttle, domeinen, unsubscribe, tracking pixel)  
  - Mogelijkheid tot aanpassen van unsubscribe-tekst en tracking toggle  
  - Read-only weergave van verzendvenster, throttle en domeinen (hard-coded in MVP)  
  - Huidig kanaal (SMTP Vimexx) zichtbaar als badge  
- **Niet in scope (MVP):**
  - Dynamisch beheren van domeinen (toevoegen/verwijderen)  
  - Wisselen tussen mailproviders (read-only toggle voor toekomst)  
  - Automatische DNS-checks (handmatig invullen/monitoren is later)

---

## 1) UI-structuur & states
### 1.1 Verzendinstellingen
- **Velden (read-only in MVP):**  
  - Tijdzone: **Europe/Amsterdam**  
  - Verzendvenster: **ma–vr, 08:00–17:00**  
  - Throttle: **1 e-mail / 20 min / per domein**  
- **Domeinenlijst:** 4 actieve domeinen zichtbaar (read-only).  
- **Toekomst:** domeinenbeheer (niet in MVP).

### 1.2 Unsubscribe
- **Tekstveld:** standaard “Uitschrijven” → editable.  
- **Landingspagina URL:** auto-gegenereerd door backend, read-only tonen.  
- **Voorbeeld:** “Link in e-mail toont: [Uitschrijven] → /unsubscribe?m=...”.

### 1.3 Tracking
- **Pixel-tracking toggle:** Aan/Uit (default Aan).  
- Tooltip: “Voegt 1×1 pixel toe om opens te meten.”  

### 1.4 E-mail infrastructuur
- **Kanaal (read-only):** SMTP (Vimexx) badge.  
- **Provider (future):** Postmark/SES toggle (disabled in MVP).  
- **DNS-checklist (read-only):** SPF, DKIM, DMARC status (handmatig ingevuld).  
- Toekomst: automatische validatie.  

---

## 2) Data & modellen (conceptueel)
- **settings**:  
  - `timezone` (string, default “Europe/Amsterdam”)  
  - `sending_window_start` (time, default 08:00)  
  - `sending_window_end` (time, default 17:00)  
  - `sending_days` (array, default [Mon–Fri])  
  - `throttle_minutes` (int, default 20)  
  - `domains[]` (array, strings; hard-coded in MVP, read-only)  
  - `unsubscribe_text` (string, default “Uitschrijven”)  
  - `unsubscribe_url` (generated, string)  
  - `tracking_pixel_enabled` (bool, default true)  
  - `provider` (string, default “SMTP”, options: smtp/postmark/ses)  
  - `dns_spf`, `dns_dkim`, `dns_dmarc` (string: ok|nok|unchecked)  

---

## 3) Gebruik & koppelingen
- **Campagnes** lezen instellingen voor venster/throttle/domeinen (read-only in MVP).  
- **Templates** gebruiken unsubscribe-tekst en tracking toggle.  
- **Berichten** bevatten unsubscribe-header + pixel indien enabled.  

---

## 4) API-contracten (zonder code)
- `GET /settings` → `{ timezone, window, throttle, domains, unsubscribe_text, unsubscribe_url, tracking_pixel_enabled, provider, dns_status }`  
- `POST /settings` → partial update (alleen `unsubscribe_text`, `tracking_pixel_enabled`).  
- (Future) `POST /settings/domains` voor domeinbeheer.  
- (Future) `POST /settings/provider` voor mailprovider-wissel.  

---

## 5) Validaties & foutafhandeling
- **Unsubscribe tekst:** min. 1, max. 50 karakters.  
- **Tracking toggle:** bool, default true.  
- **Domains:** read-only → foutmelding bij wijzigpoging in MVP.  
- **Provider:** alleen “SMTP” toegestaan in MVP.  
- **DNS-checklist:** read-only, tonen “onbekend” of “handmatig ingevuld”.  

---

## 6) Performance & schaal
- Instellingen klein; 1 record of key-value store (singleton).  
- Cachen in memory (in backend service) voor snelle lookups.  
- Updaten via `POST /settings` invalidates cache.  

---

## 7) Beveiliging & privacy
- Auth verplicht voor toegang tot settings.  
- Alleen admins (in MVP: alle gebruikers van het team) mogen wijzigen.  
- Unsubscribe URL bevat secure token (niet guessable).  

---

## 8) Telemetrie & logging
- **Events:** `settings_viewed`, `settings_updated`.  
- **Metrics:** frequentie toggle wijzigingen, unsubscribe tekstwijzigingen.  

---

## 9) QA-checklist & acceptatiecriteria
**Verzendinstellingen**  
- [ ] Tijdzone, venster en throttle zichtbaar en correct (read-only).  
- [ ] Domeinenlijst toont juiste 4 domeinen.  

**Unsubscribe**  
- [ ] Tekst kan aangepast worden en wordt opgeslagen.  
- [ ] URL is read-only, zichtbaar en klikbaar (test redirect).  

**Tracking**  
- [ ] Toggle zichtbaar en standaard Aan.  
- [ ] Uitzetten → geen pixel toegevoegd in nieuwe mails.  

**E-mail infrastructuur**  
- [ ] Kanaalbadge SMTP zichtbaar.  
- [ ] Provider toggle disabled in MVP.  
- [ ] DNS-status zichtbaar als ok/nok/onbekend.  

**Beveiliging**  
- [ ] Alleen geauthenticeerde users.  
- [ ] Unauthorized → 401.  

---

## 10) Dependencies & volgorde
1. **SCHEMA.md**: tabel/record `settings`.  
2. **Endpoints**: GET + POST (limited updates).  
3. **Frontend**: UI-secties (Verzendinstellingen, Unsubscribe, Tracking, E-mailinfra).  
4. **Integratie**: unsubscribe tekst en tracking pixel in mailer.  
5. **QA**: wijzig unsubscribe tekst + toggling pixel → effect zichtbaar in mails.  

---

## 11) Definition of Done (Instellingen)
- Instellingenscherm toont alle velden correct (read-only of editable per MVP-scope).  
- Unsubscribe-tekst kan gewijzigd worden en verschijnt in nieuwe e-mails.  
- Tracking toggle werkt (wel/niet pixel in mails).  
- Domeinen, venster, throttle en provider zijn zichtbaar als read-only.  
- DNS-status zichtbaar (handmatig ingevuld).  
- Auth, logging en privacy gegarandeerd.  
