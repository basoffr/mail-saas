# 📧 Private Mail SaaS – README

## 🚀 Overzicht
Dit project is een **private SaaS** waarmee batches van leads (bijvoorbeeld 2.100 stuks) kunnen worden geïmporteerd, verrijkt en gemaild. Het platform ondersteunt campagnes met throttling, per-lead variabelen en afbeeldingen, follow-up mails met optionele rapportbijlagen, en basisstatistieken (verstuurd + opens).

### 🌐 Architectuur
- **Frontend**: React (Next.js) via **Vercel**. UI gegenereerd met Lovable.
- **Backend**: Python (**FastAPI**) via **Render**. Background tasks/scheduler draaien in dezelfde service (MVP) of als aparte worker.
- **Database & Storage**: **Supabase** (Postgres + file storage + auth).
- **E-mail**: Initieel via **SMTP (Vimexx)**, later integratie met **Postmark** of **AWS SES**.
- **Auth**: Supabase Auth (email/tokens).

### 📊 MVP Features
- **Leads**: Excel-import, variabelen per lead, afbeeldingen per lead, detail & filters.
- **Campagnes**: Wizard (Basis → Doelgroep → Verzendregels → Review), throttling (1 per 20 min/domein), sending window (ma–vr 08–17), follow-up mails met optionele rapportbijlage.
- **Templates**: Hard-coded in backend, zichtbaar in UI, variabelen & per-lead afbeeldingen (CID rendering), preview & testsend.
- **Rapporten**: Upload & koppelen aan lead/campagne, bulk ZIP upload met mapping.
- **Statistieken**: Sent + opens, per campagne/domein/global, export CSV.
- **Instellingen**: Domeinenlijst (read-only), verzendvenster/throttle (read-only), unsubscribe configuratie, tracking pixel toggle.

### ⚙️ Kernbegrippen
- **Variabelen**:
  - `lead.*` → velden van de lead (email, bedrijf, url, image_key, …)
  - `vars.*` → extra velden uit Excel (vrij veld)
  - `campaign.*` → metadata campagne
- **Afbeeldingen**:
  - Per-lead: `{{image.cid 'hero'}}` → asset gekoppeld via lead.image_key
  - Statisch: `{{image.url 'logo'}}`
- **Tracking**: 1×1 pixel voor opens, unsubscribe link met token → suppressie.

### 🛠️ Installatie (lokaal)
#### Vereisten
- Python 3.11+
- Node.js 18+
- Docker (optioneel, voor Postgres/Redis lokaal)

#### Backend starten
```bash
cd backend
cp .env.example .env
# Vul env-vars in (Supabase, SMTP of provider)
uvicorn app.main:app --reload
```

#### Frontend starten
```bash
cd frontend
npm install
npm run dev
```

#### Database
- Supabase project aanmaken → env-vars toevoegen.
- Lokaal alternatief: Docker Postgres + seed script.

### 🚀 Deploy
- **Frontend**: push naar Vercel.
- **Backend**: push naar Render (API service + evt. worker service).
- **Database**: Supabase (managed).

### 📑 Verdere documentatie
- [`IMPLEMENTATIONPLAN.md`](./IMPLEMENTATIONPLAN.md) – fasering & MVP-scope
- [`RULES.md`](./RULES.md) – coding conventions & afspraken
- [`API.md`](./API.md) – endpoints & payloads
- [`SCHEMA.md`](./SCHEMA.md) – database ontwerp

---
© 2025 – Private Mail SaaS

