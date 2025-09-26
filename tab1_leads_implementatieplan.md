# Tab 1 — Leads (Implementatieplan)

## 0) Doel & scope
- **Doel:** Leads beheren en importeren (incl. per-lead variabelen en per-lead afbeeldingen), zodat campagnes doelgroepen kunnen selecteren en templates correct kunnen renderen.
- **In scope (MVP):**
  - Lijst + filters/zoek
  - Detail/drawer met variabelen en afbeelding-preview
  - Excel-import wizard met mapping → upsert
  - Afbeeldingskoppeling via `image_key` of `image_url`
  - Bulk selectie → doorgeven aan Campagnes
- **Niet in scope (MVP):**
  - Inline lead-bewerken
  - Geavanceerde segment-builder (valt onder Campagnes)
  - Soft-delete/archiveren

---

## 1) UI-structuur & states
### 1.1 Lijst
- **Kolommen (vast per MVP):** Email (required), Bedrijfsnaam, URL (of Domein), Tags (optioneel), Status (active|suppressed|bounced), Laatst gemaild, Laatste open, Image key (string), Vars (badge met count).
- **Acties (per rij):** Bekijken (drawer), Selecteer (checkbox).
- **Bulk acties:** “Aan campagne toevoegen” (stuurt selectie door naar Campagne-wizard).
- **Paginatie:** standaard 25 per pagina; server-side.
- **Filters:** `status`, TLD (afgeleid uit domein/url), `has_image` (ja/nee), `has_var` (keynaam), datumrange “laatst gemaild”.
- **Zoeken:** vrije tekst over email, bedrijfsnaam, domein.
- **Lege staat:** CTA “Importeer leads (Excel)”.

### 1.2 Drawer / Detail
- **Secties:**
  - Basis: email, bedrijfsnaam, url/domein, status, tags.
  - Afbeelding: preview (indien aanwezig) of placeholder; toon `image_key`.
  - Variabelen (Vars): read-only JSON viewer met key→value.
  - Historie: laatst gemaild, laatste open.
- **Acties:** “Test render” (selecteer template → server-side preview in modal, HTML + text), “Sluiten”.

### 1.3 Import wizard (3 stappen)
- **Stap 1 Upload:** accepteer .xlsx/.csv (≤ 20 MB). Toon bestandsnaam en detected sheet.
- **Stap 2 Mapping:** toon kolommen links, app-velden rechts:
  - Verplicht: **email** (of hard fail)
  - Aanbevolen: **url** (domein kan afgeleid worden)
  - Optioneel: **bedrijfsnaam**, **image_key** **of** **image_url**, overige kolommen → `vars.*`
  - Preview 20 rijen “post-mapping”
  - Dedupe/upsert-policy tonen (zie §4)
- **Stap 3 Bevestig:** samenvatting (nieuw/updated/geskipt), start import → progress + link naar resultaten (job id).

---

## 2) Datavelden & normalisatie
- **Lead kernvelden:**  
  `id (uuid)`, `email (unique, required)`, `company`, `url`, `domain` (uit `url`), `status (active|suppressed|bounced)`, `tags[]`, `image_key (string)`, `last_emailed_at (ts)`, `last_open_at (ts)`, `created_at`, `updated_at`.
- **Vars (jsonb):** alle extra kolommen uit Excel, met key-normalisatie: trim, lower, spaties/.-/→ `_`.
- **Afgeleiden:**
  - `domain` = host van `url` (zonder `www.`).
  - `tld` = suffix van `domain` (voor filter).

---

## 3) Afbeeldingen per lead
- **Route A (aanbevolen):** `image_key` in Excel, assets upload via “Rapporten → Bulk afbeeldingen” (ZIP). Matching op identieke key.  
- **Route B:** `image_url` in Excel → backend downloadt, slaat op als asset, genereert `image_key` (deterministisch op checksum of bestandsnaam).
- **Validatie assets:** PNG/JPG, ≤ 2 MB, virus-scan (basis), bewaar: `key`, `mime`, `size`, `storage_path`, `checksum`.
- **Rendering contract (voor Templates):** per-lead afbeelding via `{{image.cid 'hero'}}` resolve’t naar asset op basis van `image_key` (1-op-1 of via mapping “slot → key” als jullie dat later willen).

---

## 4) Importlogica (upsert & dedupe)
- **Primary key:** `email`.
- **Upsert regels:**
  - Nieuwe rij → **insert**.
  - Bestaande `email` → **update**: overschrijf basisvelden als niet leeg; `vars` **merge** (key per key).
  - `image_key` leeg → niet overschrijven bestaande `image_key`.
- **Skip regels:**
  - Rijen zonder valide email → skip met foutmelding.
  - Duplicaten binnen hetzelfde bestand (zelfde email) → hou eerste, rest skip (log).
- **Rapportage import:** aantallen `inserted/updated/skipped`, lijst met eerste 50 fouten (downloadbare CSV).

---

## 5) API-contracten (zonder code, referenties)
- `GET /leads` → lijst met filters/zoek/paginatie.
- `GET /leads/{id}` → detail (incl. vars, image preview URL).
- `POST /import/leads` (multipart file) → `{inserted, updated, skipped, jobId}`.
- (Optioneel) `GET /import/jobs/{jobId}` → progress & fouten.
- `GET /assets/image-by-key?key=...` → signed URL (tijdelijk).
- `POST /previews/render` → payload `{template_id, lead_id}` → `{html, text, warnings[]}`.
- **Beveiliging:** alle routes auth vereist (Supabase JWT), rate-limit basis.

---

## 6) Validaties & foutafhandeling
- **Upload:** bestandstype/size, sheet leesbaar, kolommen detecteerbaar.
- **Mapping:** minstens `email` gemapt; waarschuwing als `url` ontbreekt (geen `domain` afleiding).
- **Email:** basis regex + MX check (optioneel async), invalid → skip met reden.
- **Image:** voor route B download-fouten → markeer asset als failed en log in importrapport; lead blijft bruikbaar.
- **Drawer preview:** ontbrekende variabelen → toon waarschuwing (geen hard fail).

---

## 7) Performance & schaal
- **Paginatie server-side** met indexen op `email`, `domain`, `status`, `last_emailed_at`.
- **Import asynchroon** (job), batch inserts (100–500 rows per chunk).
- **Vars opslag** in `jsonb`, index op veelgebruikte keys (later).
- **Signed URLs** voor image preview om N+1 te voorkomen (cache headers).

---

## 8) Beveiliging & privacy
- **Auth:** Supabase JWT; alle endpoints (behalve tracking elders) vereisen auth.
- **PII:** email/adres in Postgres; opslag versleuteld at rest (Supabase).
- **Least privilege:** uploads alleen naar eigen bucket/pad; validatie mime/size.
- **Audit:** log importerende user + timestamp.

---

## 9) Telemetrie & logging
- **Events:** `leads_import_started/succeeded/failed`, `lead_viewed`, `lead_preview_rendered`.
- **Metrics:** importduur, aantal rijen/min, skip reasons count.
- **Logs:** per importregel bij fout (max 50 inline, rest CSV download).

---

## 10) QA-checklist & acceptatiecriteria
**Lijst & filters**
- [ ] Paginatie werkt, filters combineren (status + TLD + has_image).
- [ ] Zoek op email/bedrijf/domein retourneert juiste subset.
- [ ] Bulkselectie bewaart selectie over paginatie (of expliciet niet—UI duidelijk).

**Drawer**
- [ ] Vars JSON leesbaar, grote waarden afgekapt met “toon meer”.
- [ ] Image preview toont bij geldige `image_key`; anders placeholder + hint.

**Import**
- [ ] .xlsx en .csv beide ondersteund.
- [ ] Mapping verplicht email, optioneel url/bedrijfsnaam/image_key.
- [ ] Upsert: bestaande lead update, vars merge (bestaande keys overschrijfbaar).
- [ ] Rapport: inserted/updated/skipped aantallen kloppen; fouten CSV beschikbaar.

**Afbeeldingen**
- [ ] Route A: ZIP upload → keys matchen → preview zichtbaar.
- [ ] Route B: image_url downloadt en slaat op; bij fout blijft lead bruikbaar.

**Preview render**
- [ ] Kiezen van template + lead rendeert HTML + text.
- [ ] Warnings tonen bij ontbrekende vars of missende afbeelding.

**Beveiliging**
- [ ] Auth verplicht; 401 bij ontbrekende/ongeldige token.
- [ ] Alleen geautoriseerde users kunnen importeren.

**Performance**
- [ ] Import 2.100 rijen < X minuten (acceptabel voor MVP).
- [ ] Lijst response < 500 ms bij 25 rijen (zonder zware filters).

---

## 11) Dependencies & volgorde
1. **SCHEMA.md**: tabellen `leads`, `assets`, (optioneel) `import_jobs`.
2. **API endpoints** uitwerken (zoals in API.md).
3. **Frontend** lijst + filters + drawer + wizard (stap 1–3).
4. **Import job** + rapportage.
5. **Afbeeldingsflow** (ZIP + image_url).
6. **Preview render** endpoint koppelen.
7. **QA & acceptatie** volgens §10.

---

## 12) “Definition of Done” (Leads)
- Gebruiker kan een Excel importeren, mapping doen, en binnen enkele minuten resultaten zien (inserted/updated/skipped + fouten).
- Leads zijn zichtbaar, filterbaar en doorzoekbaar; detail toont vars en afbeelding.
- Per-lead preview van template werkt en toont waarschuwingen.
- Bulkselectie kan door naar Campagnes-wizard.
- Security, logging en basis-telemetrie aanwezig.
