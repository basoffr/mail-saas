# 🌀 Windsurf Superprompt – Tabblad 6 (Instellingen)

Lees eerst zorgvuldig de volgende projectbestanden in:  
- `api.md`  
- `rules.md`  
- `readme.md`  
- `implementationplan.md`  
- `tab6_instellingen_implementatieplan.md`  
- `lovable-prompts.md`  
- `schema.md` (indien aanwezig)  

⚠️ Pas **uitsluitend code aan die relevant is voor Tabblad 6 (Instellingen)**.  
Andere modules (Leads, Templates, Campagnes, Rapporten, Statistieken) mogen **niet** aangepast worden.  

---

## ✅ Opdracht

### 1. Router & Endpoints
- Maak `api/settings.py` met endpoints exact volgens **API.md** en **tab6_instellingen_implementatieplan.md**:
  - `GET /settings` → retourneer configuratie `{timezone, window, throttle, domains[], unsubscribe_text, unsubscribe_url, tracking_pixel_enabled, provider, dns_status}`.  
  - `POST /settings` → partial update, alleen `unsubscribe_text` en `tracking_pixel_enabled` mogen aangepast worden in MVP.  

- Response-shape uit `rules.md` `{data:..., error:null}`.  
- Auth verplicht via Supabase JWT.  
- Logging events: `settings_viewed`, `settings_updated`.

---

### 2. Model & Schema
- **Settings** (singleton record of key-value store):  
  - `timezone` (string, default Europe/Amsterdam).  
  - `sending_window_start` (08:00), `sending_window_end` (17:00).  
  - `sending_days` ([Mon–Fri]).  
  - `throttle_minutes` (20).  
  - `domains[]` (hard-coded in MVP, read-only).  
  - `unsubscribe_text` (string, default “Uitschrijven”).  
  - `unsubscribe_url` (auto gegenereerd, read-only).  
  - `tracking_pixel_enabled` (bool, default true).  
  - `provider` (string, default SMTP).  
  - `dns_spf`, `dns_dkim`, `dns_dmarc` (enum ok|nok|unchecked).  

- Pydantic schemas: `SettingsOut`, `SettingsUpdate`.

---

### 3. Services
- **services/settings.py**:  
  - Ophalen en cachen van instellingen (singleton).  
  - Update unsubscribe_text (1–50 chars).  
  - Toggle tracking_pixel_enabled (bool).  
  - Invalidate cache na update.  
  - Generate unsubscribe_url met secure token.  
  - DNS-checks: nu read-only, later uitbreidbaar naar automatische validatie.  

---

### 4. Validaties & Beveiliging
- Alleen `unsubscribe_text` en `tracking_pixel_enabled` mogen gewijzigd worden in MVP.  
- Domeinen, venster, throttle en provider zijn read-only.  
- Unsubscribe_text min. 1 max. 50 karakters.  
- Provider = “SMTP” verplicht in MVP.  
- Auth verplicht (JWT).  
- Alleen admin/teamleden mogen aanpassen.  

---

### 5. Tests & Fixtures
- Pytest-tests:  
  - GET /settings → alle velden correct (read-only vs editable).  
  - POST /settings → unsubscribe_text update slaagt, tracking toggle werkt.  
  - Ongeldige unsubscribe_text (>50 chars) → foutmelding.  
  - Proberen domeinen/provider te wijzigen → foutmelding.  

- Fixtures: sample settings-record.  

---

### 6. Definition of Done
- Instellingenscherm toont alle velden correct (read-only of editable).  
- Unsubscribe-tekst kan gewijzigd worden en verschijnt in nieuwe mails.  
- Tracking toggle werkt (wel/niet pixel in mails).  
- Domeinen, venster, throttle en provider zichtbaar als read-only.  
- DNS-status zichtbaar (ok/nok/onbekend).  
- Auth, logging en privacy conform rules.md.  
- QA-checklist in `tab6_instellingen_implementatieplan.md` volledig groen.  

---
