# Tab 5 — Statistieken (Implementatieplan)

## 0) Doel & scope
- **Doel:** Inzicht geven in verzendprestaties op **globaal**, **per domein** en **per campagne** niveau, op basis van MVP-metrics: **sent** en **opens** (via tracking pixel), plus **bounces** als teller.
- **In scope (MVP):**
  - Overzichtskpi’s (global)
  - Segmenten: per domein, per campagne
  - Tijdlijn-grafieken (per dag)
  - CSV-export (globaal / per domein / per campagne)
- **Niet in scope (MVP):**
  - Click/reply metrics
  - Geavanceerde cohort- of funnel-analyses

---

## 1) UI-structuur & states
### 1.1 Overzicht (Global)
- **KPI-tegels:**
  - **Totaal verstuurd** (sum messages with status=sent)
  - **Open rate** (opens / sent)
  - **Bounces** (count status=bounced)
- **Tijdlijn:** lijn- of staafgrafiek “**Verstuurd per dag**” en “**Opens per dag**” (toggle of 2 grafieken).
- **Filters:**
  - Datumbereik (default: laatste 30 dagen)
  - Template (optioneel)
- **Acties:** **Export CSV (global)**

### 1.2 Per domein
- **Tabel:** `Domein | Verstuurd | Open rate | Bounces | Laatste activiteit`
- **Sorteren:** op verstuurd / open rate / bounces
- **Acties:** **Export CSV (per domein)**  
- **Detail popover (optioneel):** kleine tijdlijn voor gekozen domein.

### 1.3 Per campagne
- **Tabel:** `Campagne | Startdatum | Verstuurd | Open rate | Bounces | Status`
- **Acties:** link naar **Campagne-detail**
- **Acties:** **Export CSV (per campagne)**

---

## 2) Data & modellen (conceptueel)
- **messages**: `id`, `campaign_id`, `lead_id`, `domain_used`, `scheduled_at`, `sent_at`, `status (queued|sent|bounced|opened|failed)`, `open_at (nullable)`, `last_event_at`.
- **message_events** (optioneel): `message_id`, `type (sent|open|bounce|failed)`, `created_at`, `meta`.
- **Aggregaties** worden berekend op basis van `messages` (MVP: zonder aparte warehousing).

**Definities:**
- **Sent:** `status = sent` of event `sent` geregistreerd.
- **Open:** `open_at not null` of event `open` ≥ 1 (MVP telt uniek per message).
- **Bounce:** `status = bounced` (hard bounces); soft retries tellen niet mee.

---

## 3) Aggregatie & berekening (functioneel)
- **Global KPIs** (binnen geselecteerd datumbereik):
  - `total_sent = count(messages where sent_at within range)`
  - `total_opens = count(messages where open_at within range)`
  - `open_rate = total_opens / total_sent` (0 als noemer 0)
  - `bounces = count(messages where status=bounced and event_time within range)`
- **Tijdlijn per dag:**
  - `sent_by_day[date] = count(sent_at on date)`
  - `opens_by_day[date] = count(open_at on date)`
- **Per domein:**
  - Groepeer op `domain_used`: `sent`, `opens`, `open_rate`, `bounces`, `last_event_at (max)`
- **Per campagne:**
  - Groepeer op `campaign_id`: zelfde set + `status` uit `campaigns`.

**Prestatie-optimalisatie (MVP):**
- Directe SQL met indexen volstaat bij <100k messages.
- Eventuele eenvoudige **materialized views**:
  - `daily_stats(date, sent, opens)` voor global
  - `domain_daily_stats(date, domain, sent, opens)` (optioneel)
  - `campaign_daily_stats(date, campaign_id, sent, opens)` (optioneel)

---

## 4) API-contracten (zonder code)
- `GET /stats/summary?from=YYYY-MM-DD&to=YYYY-MM-DD&template_id?`
  - Response: `{ global:{...}, domains:[...], campaigns:[...], timeline:{sentByDay[], opensByDay[]} }`
- `GET /stats/export?scope=global|domain|campaign&from=...&to=...&id?`
  - Response: CSV-bestand
- (Optioneel) `GET /stats/domains?from=...&to=...`
- (Optioneel) `GET /stats/campaigns?from=...&to=...`

---

## 5) Validaties & foutafhandeling
- **Datumbereik:** `from ≤ to`, max 365 dagen (MVP).
- **Lege datasets:** toon `0`-waarden en lege grafieken i.p.v. error.
- **Export:** CSV headers consistent, komma-gescheiden, datums in ISO (`YYYY-MM-DD`).

---

## 6) Performance & schaal
- **Indexen:**  
  - `messages(sent_at)`, `messages(open_at)`, `messages(domain_used)`, `messages(campaign_id)`  
  - Composiet waar nuttig: `(campaign_id, sent_at)`, `(domain_used, sent_at)`
- **Caching (optioneel):** cache response van `stats/summary` 60s voor hetzelfde datumbereik + filters.
- **Paginatie:** nodig voor per-campagne tabel (indien veel campagnes).

---

## 7) Beveiliging & privacy
- **Auth verplicht** voor alle stats endpoints.
- **Data scope:** single-team; geen cross-tenant lekken.
- **Geen PII in export** buiten e-maildomeinen of campagnenamen; exports bevatten geen e-mailadressen op dit tabblad (alleen geaggregeerd).

---

## 8) Telemetrie & logging
- **Events:** `stats_viewed` (met scope en filters), `stats_exported` (scope).
- **Metrics:** latency van stats queries, cache hit-rate (indien cache), rijen verwerkt.

---

## 9) QA-checklist & acceptatiecriteria
**Global**
- [ ] KPI-tegels tonen correcte waarden binnen range.
- [ ] Tijdlijn sent/opens klopt met ruwe data (spot-check).

**Per domein**
- [ ] Tabelwaarden (sent, open rate, bounces) kloppen; sorteren werkt.
- [ ] Export CSV bevat dezelfde aggregaties.

**Per campagne**
- [ ] Tabelwaarden kloppen; link naar campagnedetail werkt.
- [ ] Export CSV per campagne bevat juiste kolommen.

**Edge cases**
- [ ] Geen data → geen errors; nette lege staat.
- [ ] Datumbereik in weekend/geen verzending → grafieken leeg.

**Prestaties**
- [ ] Stats call < 700ms bij 2.1k messages (MVP).
- [ ] Export CSV genereert binnen acceptabele tijd (< 3s).

---

## 10) Dependencies & volgorde
1. **SCHEMA.md:** `messages` velden incl. `sent_at`, `open_at`, `status`, `domain_used`, `campaign_id`.
2. **Tracking pixel** endpoint live (zodat `open_at` gevuld wordt).
3. **Aggregatie-queries** definiëren (SQL) & endpoints implementeren.
4. **Frontend**: KPI-tegels, tijdlijn grafieken, tabellen en exports.
5. **QA**: validatie tegen steekproef uit `messages`.

---

## 11) Definition of Done (Statistieken)
- Overzicht toont correcte totals en open rate.
- Segmenten per domein & per campagne werken met filters en export.
- Tijdlijn werkt en is consistent met totals.
- Auth & privacy gewaarborgd; performance acceptabel.
