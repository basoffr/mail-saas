# Tab 4 — Rapporten (Implementatieplan)

## 0) Doel & scope
- **Doel:** Rapporten (bijv. PDF/XLSX/PNG) uploaden en koppelen aan leads of campagnes, zodat ze in follow-up mails als bijlage kunnen worden meegestuurd.  
- **In scope (MVP):**
  - Rapportenoverzicht met filters
  - Single upload + koppelen aan lead of campagne
  - Bulk upload (ZIP) met automatische mapping via `image_key` of `email`
  - Koppelen/ontkoppelen van bestaande rapporten
  - Gebruik van rapporten in follow-ups
- **Niet in scope (MVP):**
  - Automatisch genereren van rapporten uit crawl/scrape data
  - Inline bewerken of preview van inhoud

---

## 1) UI-structuur & states
### 1.1 Overzicht
- **Kolommen:** Bestandsnaam, Type (pdf/xlsx/png/jpg), Grootte (KB/MB), Gekoppeld aan (lead-email of campagne-naam), Upload-datum.  
- **Acties per rij:** Bekijken details, Download, Ontkoppelen.  
- **Filters:** type (pdf/xlsx/png/jpg), gekoppeld/ongekoppeld, datumrange.  
- **Lege staat:** CTA “Upload rapport”.

### 1.2 Upload — Single
- **Inputs:** bestand selecteren (max 10MB), type detectie automatisch.  
- **Koppelen aan:**  
  - Lead (zoek op email)  
  - Campagne (zoek op naam)  
- **Actie:** Upload → bevestiging.  

### 1.3 Upload — Bulk (ZIP)
- **Inputs:** ZIP selecteren (max 100MB, ≤ 100 bestanden).  
- **Mapping-methode (radio):**
  - By `image_key` (map keys → rapportbestanden)  
  - By `email` (match bestandsnaam/email → lead)  
- **Preview mapping:** lijst van matches en niet-gematchte bestanden.  
- **Validatie:** max 10MB per bestand in ZIP, alleen toegestane types.  
- **Actie:** Upload → bulk mapping uitvoeren → rapportage “X gekoppeld, Y niet herkend”.  

### 1.4 Detail / Koppeling
- **Velden:** bestandsnaam, type, grootte, gekoppeld aan, upload-datum.  
- **Acties:** Ontkoppelen, Download.  
- **Lead/Campagne-link:** klikbaar → opent detailpagina lead/campagne.

---

## 2) Data & modellen (conceptueel)
- **reports**:  
  - `id (uuid)`, `filename`, `type`, `size`, `storage_path`, `checksum`, `created_at`, `uploaded_by`.  
- **report_links**:  
  - `report_id`, `lead_id (nullable)`, `campaign_id (nullable)`, `created_at`.  
- Constraints: een rapport kan aan meerdere entiteiten worden gekoppeld (multi-link toegestaan, maar in MVP 1:1 is ook prima).  

---

## 3) Gebruik in campagnes/follow-ups
- Bij follow-up scheduling:  
  - **Als attach_report = true** in campagne:  
    - Zoek gekoppeld rapport aan lead.  
    - Indien geen lead-rapport: kijk of campagne-rapport beschikbaar is.  
    - Bij geen match: geen bijlage, maar mail wordt alsnog verzonden.  
- Bijlage als **MIME attachment** bij de e-mail; max 1 rapport per bericht in MVP.  

---

## 4) API-contracten (zonder code)
- `GET /reports` → lijst + filters.  
- `POST /reports/upload` → multipart file + optional `{lead_id|campaign_id}`.  
- `POST /reports/bulk?mode=by_image_key|by_email` → ZIP upload; response = mapping-resultaat.  
- `POST /reports/bind` → payload `{report_id, lead_id|campaign_id}`.  
- `POST /reports/unbind` → payload `{report_id}`.  
- `GET /reports/{id}/download` → signed URL of binary.  

---

## 5) Validaties & foutafhandeling
- **Upload:**  
  - Bestandstype toegestaan (pdf/xlsx/png/jpg).  
  - Max 10MB.  
  - Virus/mime-check.  
- **Bulk upload:**  
  - ZIP max 100MB, max 100 files.  
  - Bestandsnamen uniek binnen ZIP.  
  - Mislukte matches → in rapportage teruggegeven.  
- **Bind/Unbind:**  
  - Lead/campagne moet bestaan.  
  - Rapport moet bestaan.  
- **Download:**  
  - Signed URL 5 minuten geldig.  
  - Alleen geauthenticeerde users.  

---

## 6) Performance & schaal
- Bestanden opslaan in **Supabase storage bucket** `reports/`.  
- Metadata in DB (`reports` + `report_links`).  
- Bulk-uploads asynchroon verwerken (jobs per bestand), maar kleine batches (≤100) kunnen synchroon in MVP.  
- Index op `report_links` voor snelle lookup (lead_id, campaign_id).  

---

## 7) Beveiliging & privacy
- **Auth:** alle endpoints achter Supabase JWT.  
- **Access control:** single-team SaaS, geen cross-org leakage.  
- **Storage:** per bestand checksum + mime-check → voorkomt spoofing.  
- **GDPR:** rapporten bevatten mogelijk PII → bewaarbeleid max X maanden (instelbaar later).  

---

## 8) Telemetrie & logging
- **Events:** `report_uploaded`, `report_bound`, `report_unbound`, `report_downloaded`.  
- **Metrics:** aantal rapporten, storage volume, uploads per dag.  
- **Fouten:** percentage onherkende bulk-matches.  

---

## 9) QA-checklist & acceptatiecriteria
**Overzicht**  
- [ ] Lijst toont juiste bestandsinfo, gekoppeld aan lead/campagne.  
- [ ] Filters werken (type, gekoppeld/ongekoppeld).  

**Single upload**  
- [ ] Upload van 1 bestand < 10MB werkt; koppeling correct.  
- [ ] Ongeldig bestandstype → nette foutmelding.  

**Bulk upload**  
- [ ] ZIP < 100MB met ≤100 bestanden werkt.  
- [ ] Mapping preview toont matches en niet-herkende bestanden.  
- [ ] Resultaat “X gekoppeld, Y niet herkend” klopt.  

**Detail**  
- [ ] Download levert geldig bestand.  
- [ ] Ontkoppelen verwijdert link maar bestand blijft bestaan.  

**Follow-up integratie**  
- [ ] Campagne met attach_report true → rapport meegestuurd indien beschikbaar.  
- [ ] Geen rapport beschikbaar → mail alsnog verstuurd zonder bijlage.  

**Beveiliging**  
- [ ] Alleen geauthenticeerde users.  
- [ ] Downloadlink vervalt na TTL.  

---

## 10) Dependencies & volgorde
1. **SCHEMA.md:** tabellen `reports`, `report_links`.  
2. **Endpoints** (upload, bulk, bind/unbind, list, download).  
3. **Frontend** overzicht + uploadformulieren + bulk upload preview.  
4. **Integratie** in campagne-follow-up flow.  
5. **QA** op uploads, bulk mapping, koppelingen en follow-up verzending.  

---

## 11) Definition of Done (Rapporten)
- Rapporten kunnen worden geüpload (single + bulk) en gekoppeld aan leads/campagnes.  
- Rapporten zijn zichtbaar in lijst, filterbaar en downloadbaar.  
- Follow-ups kunnen optioneel rapporten meesturen als bijlage.  
- Auth, logging en basis-telemetrie aanwezig.  
