# 🌐 Deploy & Configuratie Opzet (Windsurf)

## 0) Doel & Scope
- **Frontend** → Vercel  
- **Backend (FastAPI)** → Render Web Service  
- **DB/Storage/Auth** → Supabase  
- Consistente API-responses `{data, error}` + auth via Supabase JWT.  
- Health endpoints aanwezig voor monitoring/cutover.

---

## 1) Repo & Configuratie
- Projectstructuur valideren (frontend/backend/tests/requirements).  
- CORS activeren op backend voor frontend-domein.  
- **`.env.example` (FE & BE)** toevoegen met placeholders (Supabase, SMTP, buckets, limits).  
- Check response-shape & logging (structured JSON).

---

## 2) Supabase Inrichten
1. **Keys noteren**: URL, anon, service role.  
2. **Database schema** toepassen (migraties/DDL).  
3. **Storage buckets** aanmaken:  
   - `assets` (afbeeldingen, signatures, dashboard images)  
   - `reports` (PDF/XLSX/ZIP + bulk mapping)  
4. **RLS/Policies**: backend deelt signed URLs uit (TTL ~1u) → service-role key server-side.

---

## 3) Render – Backend Web Service
- **Service type**: Web Service (Python).  
- **Build**: `pip install -r requirements.txt`  
- **Start**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
- **Health check**: `/api/v1/health`  
- **Env vars**:  
  - Supabase: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`  
  - Storage/buckets: `ASSETS_BUCKET`, `REPORTS_BUCKET`, `SIGNED_URL_TTL=3600`  
  - App: `TIMEZONE=Europe/Amsterdam`, `JWT_SECRET=...`  
  - SMTP: `SMTP_HOST`, `SMTP_PORT=587`, `SMTP_USERNAME`, `SMTP_PASSWORD`  
  - (Optioneel Inbox): `IMAP_*` / secret-ref.

---

## 4) Vercel – Frontend
- **Env vars (public)**:  
  - `NEXT_PUBLIC_SUPABASE_URL`  
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`  
  - `NEXT_PUBLIC_API_BASE_URL=https://<render-backend>/api/v1`  
- **Fixtures** uitzetten: `NEXT_PUBLIC_USE_FIXTURES=false`.

---

## 5) End-to-End Checks (Smoke Tests)
1. Leads import (CSV/XLSX) + job polling.  
2. Templates → preview + testsend (rate limiting).  
3. Campaigns → wizard → dry-run → start; throttle/venster validatie.  
4. Reports → single upload + bulk ZIP → bind/unbind → download (signed URL).  
5. Statistics → summary + CSV export (30 dagen default).  
6. Settings → GET/POST unsubscribe-text + tracking toggle.  
7. (Optioneel) Inbox/Replies → IMAP fetch testaccount → linking badges.

---

## 6) Monitoring & Cutover Validatie
- `/health` monitoren (basic + detailed).  
- Assets: signed URLs genereren, TTL 1u.  
- Reports: file-limits (10MB file / 100MB ZIP) testen.  
- CSV-export loggingvelden controleren (`with_image`, `with_report`).

---

## 7) Production Hardening
- CORS beperken tot frontend-domeinen.  
- Secrets **alleen via env**, nooit hard-coded.  
- Start met kleine instance; autoscaling later.  
- (Later) Worker/Cron los trekken voor scheduler of IMAP fetches.

Alternatieve gegevens:
Database password supabase: dULQdoLbu37xpBRk
Project URL supabase: https://zpnklihryhpkaiyubkfn.supabase.co 
API KEY Supabase: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDMzNDIsImV4cCI6MjA3NDcxOTM0Mn0.P8Rx3r--uu8V-HCEH2s5qH3Ud0HhpLBUWaidrahO0jY
github: https://github.com/basoffr/mail-saas
Render start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Render deploy-hook: https://api.render.com/deploy/srv-d3d76oggjchc739pgfn0?key=sJFps_tkht8
Render link: https://mail-saas-rf4s.onrender.com
Deployment link vercel: https://vercel.com/punthelder-admins-projects/mail-saas/pNJgntHmTjiZS3wVxsZKddRymZ7r
Domain vercel: https://mail-saas-xi.vercel.app/
Vercel project ID: prj_9ejMxCPUy5U7AwhR8yPVJhHLupRK



