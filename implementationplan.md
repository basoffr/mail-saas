# 📌 IMPLEMENTATIONPLAN – Private Mail SaaS

## 🎯 Doel
Een MVP realiseren waarmee batches leads (~2.100) volledig online geïmporteerd, beheerd, en gemaild kunnen worden, inclusief follow-up, variabele templates en basisstatistieken.

## 🚦 Fasering

### Fase 1 – Fundering (1–2 weken)
- **Backend**: FastAPI + Supabase connectie.
- **Frontend**: Vercel + Lovable UI generator.
- **Database**: Supabase schema (leads, campaigns, messages, templates, reports, stats, settings).
- **Leads import**: Excel upload + mapping → DB.
- **E-mail integratie**: SMTP (Vimexx) voor MVP.
- **Templates**: hard-coded, preview & testsend.
- **Campagnes**: aanmaken & plannen (throttle, venster, domeinen hard-coded).
- **Statistieken**: sent + opens (tracking pixel).
- **Unsubscribe**: link + suppressielijst.

### Fase 2 – Uitbreiding (1–2 weken)
- **Rapporten**: upload & koppelen (lead/campagne), bulk ZIP met mapping.
- **Follow-ups**: automatisch plannen (X dagen, bijlage optioneel).
- **Campagne detail**: berichtenlog, resend bij fouten, follow-up panel.
- **Instellingen**: domeinenlijst zichtbaar, unsubscribe-tekst bewerkbaar, tracking toggle.
- **Stats**: global/dashboard + per domein/campagne, CSV export.

### Fase 3 – Hardening (1–2 weken)
- **Error handling**: retries, exponential backoff.
- **Deliverability**: SPF/DKIM/DMARC validatie-checklist in UI.
- **Dry-run simulatie** in campagnes.
- **Validatie templates**: warnings voor ontbrekende variabelen/afbeeldingen.
- **Infra**: worker service (Render) voor scheduler & queue.

## 📊 In Scope (MVP)
- Leads: import, filteren, detail, image preview.
- Campagnes: wizard, planning, sending window, follow-up.
- Templates: preview, variabelen, testsend, images.
- Rapporten: upload + koppelen.
- Statistieken: sent, opens.
- Instellingen: domeinen, venster/throttle (read-only), unsubscribe, tracking toggle.

## 🚫 Niet in Scope (MVP)
- Automatisch rapport genereren uit crawl/scrape data.
- Click tracking.
- Reply tracking (IMAP/POP3 inbound parsing).
- Geavanceerde segmentatie UI (buiten basisfilters).
- Multi-tenant accounts (nu single-team SaaS).

## 🔧 Services
- **Frontend**: Vercel (React/Next.js, Lovable prompts).
- **Backend**: Render (FastAPI).
- **Database/Storage**: Supabase (Postgres + Storage + Auth).
- **Mail**: SMTP (Vimexx) → later Postmark/SES.

## ✅ Deliverables
- Werkende frontend met 6 tabbladen.
- Backend API met alle endpoints (zie API.md).
- Database schema & migraties (zie SCHEMA.md).
- README, RULES, API, SCHEMA docs.
- Batch van 2.100 leads verstuurd via throttle 1/20 min/domein.

---
© 2025 – Private Mail SaaS

