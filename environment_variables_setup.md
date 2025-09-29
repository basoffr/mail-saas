# 🌐 Environment Variables Setup Guide

## 📋 **OVERZICHT**

Dit document bevat alle benodigde environment variables voor de Mail Dashboard deployment op:
- **Supabase** (Database & Storage)
- **Render** (Backend FastAPI)
- **Vercel** (Frontend React)

---

## 🗄️ **SUPABASE CONFIGURATIE**

### **Dashboard Setup Checklist**

| **Taak** | **Locatie** | **Status** | **Actie** |
|----------|-------------|------------|-----------|
| **Database Schema** | SQL Editor | ❌ | Database tabellen aanmaken |
| **Storage Buckets** | Storage | ❌ | `assets` en `reports` buckets maken |
| **RLS Policies** | Storage → Policies | ❌ | Service role toegang configureren |
| **API Keys** | Settings → API | ✅ | Keys al beschikbaar |

### **1. Database Schema Migratie**
**Locatie**: Supabase Dashboard → SQL Editor
**Status**: ❌ **NOG TE DOEN**

**SQL Script uitvoeren:**
```sql
-- Leads tabel
CREATE TABLE leads (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    company VARCHAR,
    url VARCHAR,
    domain VARCHAR,
    status VARCHAR DEFAULT 'active',
    tags JSONB DEFAULT '[]',
    image_key VARCHAR,
    last_emailed_at TIMESTAMPTZ,
    last_open_at TIMESTAMPTZ,
    vars JSONB DEFAULT '{}',
    stopped BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_domain ON leads(domain);
CREATE INDEX idx_leads_stopped ON leads(stopped);

-- [ALLE ANDERE TABELLEN - campaigns, templates, etc.]
```

### **2. Storage Buckets**
**Locatie**: Supabase Dashboard → Storage
**Status**: ❌ **NOG TE DOEN**

**Buckets aanmaken:**
- `assets` (private bucket voor afbeeldingen, signatures)
- `reports` (private bucket voor PDF/XLSX bestanden)

### **3. RLS Policies**
**Locatie**: Storage → Policies
**Status**: ❌ **NOG TE DOEN**

**Policies aanmaken:**
```sql
-- Assets bucket policy
CREATE POLICY "Service role can manage assets" ON storage.objects
    FOR ALL USING (bucket_id = 'assets' AND auth.role() = 'service_role');

-- Reports bucket policy  
CREATE POLICY "Service role can manage reports" ON storage.objects
    FOR ALL USING (bucket_id = 'reports' AND auth.role() = 'service_role');
```

### **4. API Keys & Credentials**
**Locatie**: Settings → API
**Status**: ✅ **COMPLEET**

| **Credential** | **Value** |
|----------------|-----------|
| **Project URL** | `https://zpnklihryhpkaiyubkfn.supabase.co` |
| **Database Password** | `dULQdoLbu37xpBRk` |
| **Anon Key** | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDMzNDIsImV4cCI6MjA3NDcxOTM0Mn0.P8Rx3r--uu8V-HCEH2s5qH3Ud0HhpLBUWaidrahO0jY` |
| **Service Role Key** | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTE0MzM0MiwiZXhwIjoyMDc0NzE5MzQyfQ.hiXLQuSR7w4r_Hq9Rie2MyDPMaHRljgsNpC1MEyEeDs` |

### **5. Connection String**
**Voor Backend gebruik:**
```
postgresql://postgres:dULQdoLbu37xpBRk@db.zpnklihryhpkaiyubkfn.supabase.co:5432/postgres
```

---

## 🔧 **RENDER - BACKEND ENVIRONMENT VARIABLES**

### **Service Settings**
- **Service Type**: Web Service
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### **Environment Variables (41 totaal)**

| **Variable Name** | **Value** |
|------------------|-----------|
| `DATABASE_URL` | `postgresql://postgres:dULQdoLbu37xpBRk@db.zpnklihryhpkaiyubkfn.supabase.co:5432/postgres` |
| `SUPABASE_URL` | `https://zpnklihryhpkaiyubkfn.supabase.co` |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDMzNDIsImV4cCI6MjA3NDcxOTM0Mn0.P8Rx3r--uu8V-HCEH2s5qH3Ud0HhpLBUWaidrahO0jY` |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTE0MzM0MiwiZXhwIjoyMDc0NzE5MzQyfQ.hiXLQuSR7w4r_Hq9Rie2MyDPMaHRljgsNpC1MEyEeDs` |
| `ASSETS_BUCKET` | `assets` |
| `REPORTS_BUCKET` | `reports` |
| `SIGNED_URL_TTL` | `3600` |
| `USE_FIXTURES` | `false` |
| `API_TIMEOUT` | `30` |
| `TZ` | `Europe/Amsterdam` |
| `JWT_SECRET_KEY` | `14dca67c34cb97be1cedcfacf50ff424` |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
| `SMTP_HOST_MARKETING` | `mail.punthelder-marketing.nl` |
| `SMTP_HOST_SEO` | `mail.punthelder-seo.nl` |
| `SMTP_HOST_VINDBAARHEID` | `mail.punthelder-vindbaarheid.nl` |
| `SMTP_HOST_ZOEKMACHINE` | `mail.punthelder-zoekmachine.nl` |
| `SMTP_PORT` | `587` |
| `SMTP_USE_TLS` | `true` |
| `SMTP_USER_MARKETING_CHRISTIAN` | `christian@punthelder-marketing.nl` |
| `SMTP_USER_MARKETING_VICTOR` | `victor@punthelder-marketing.nl` |
| `SMTP_USER_SEO_CHRISTIAN` | `christian@punthelder-seo.nl` |
| `SMTP_USER_SEO_VICTOR` | `victor@punthelder-seo.nl` |
| `SMTP_USER_VINDBAARHEID_CHRISTIAN` | `christian@punthelder-vindbaarheid.nl` |
| `SMTP_USER_VINDBAARHEID_VICTOR` | `victor@punthelder-vindbaarheid.nl` |
| `SMTP_USER_ZOEKMACHINE_CHRISTIAN` | `christian@punthelder-zoekmachine.nl` |
| `SMTP_USER_ZOEKMACHINE_VICTOR` | `victor@punthelder-zoekmachine.nl` |
| `SMTP_PASSWORD_MARKETING_CHRISTIAN` | `[WACHTWOORD_CHRISTIAN_MARKETING]` |
| `SMTP_PASSWORD_MARKETING_VICTOR` | `[WACHTWOORD_VICTOR_MARKETING]` |
| `SMTP_PASSWORD_SEO_CHRISTIAN` | `[WACHTWOORD_CHRISTIAN_SEO]` |
| `SMTP_PASSWORD_SEO_VICTOR` | `[WACHTWOORD_VICTOR_SEO]` |
| `SMTP_PASSWORD_VINDBAARHEID_CHRISTIAN` | `[WACHTWOORD_CHRISTIAN_VINDBAARHEID]` |
| `SMTP_PASSWORD_VINDBAARHEID_VICTOR` | `[WACHTWOORD_VICTOR_VINDBAARHEID]` |
| `SMTP_PASSWORD_ZOEKMACHINE_CHRISTIAN` | `[WACHTWOORD_CHRISTIAN_ZOEKMACHINE]` |
| `SMTP_PASSWORD_ZOEKMACHINE_VICTOR` | `[WACHTWOORD_VICTOR_ZOEKMACHINE]` |
| `RATE_LIMIT_REQUESTS` | `100` |
| `RATE_LIMIT_WINDOW` | `60` |
| `MAX_FILE_SIZE_MB` | `10` |
| `MAX_BULK_SIZE_MB` | `100` |
| `MAX_BULK_FILES` | `100` |
| `LOG_LEVEL` | `INFO` |
| `CORS_ORIGINS` | `https://mail-saas-xi.vercel.app,https://mail-saas.vercel.app` |

---

## ⚡ **VERCEL - FRONTEND ENVIRONMENT VARIABLES**

### **Project Settings**
- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### **Environment Variables**
```env
# Supabase Configuration (Public)
NEXT_PUBLIC_SUPABASE_URL=https://zpnklihryhpkaiyubkfn.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDMzNDIsImV4cCI6MjA3NDcxOTM0Mn0.P8Rx3r--uu8V-HCEH2s5qH3Ud0HhpLBUWaidrahO0jY

# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://mail-saas-rf4s.onrender.com/api/v1

# Application Configuration
NEXT_PUBLIC_USE_FIXTURES=false
NEXT_PUBLIC_APP_ENV=production
```

---

## 🔐 **SECRETS DIE JE MOET GENEREREN**

### **1. JWT Secret Key**
```bash
# Genereer 256-bit random key
openssl rand -hex 32
# Of online: https://generate-secret.vercel.app/32
```

### **2. Supabase Service Role Key**
1. Ga naar Supabase Dashboard
2. **Settings** → **API** 
3. Kopieer **service_role** key (niet anon!)
4. ⚠️ **BELANGRIJK**: Houd deze geheim!

### **3. SMTP Credentials**
- Vraag aan Vimexx hosting provider
- Of configureer alternatieve SMTP (Gmail, SendGrid, etc.)

---

## 📝 **DEPLOYMENT CHECKLIST**

### **Supabase Setup**
- [ ] Database schema migreren (SQL scripts)
- [ ] Storage buckets aanmaken (`assets`, `reports`)
- [ ] RLS policies configureren
- [ ] Service role key genereren

### **Render Backend**
- [ ] Alle environment variables instellen
- [ ] Health endpoint testen: `https://mail-saas-rf4s.onrender.com/api/v1/health`
- [ ] CORS origins configureren
- [ ] Deploy hook testen

### **Vercel Frontend**
- [ ] Environment variables instellen
- [ ] Build succesvol
- [ ] API connectie testen
- [ ] Custom domain configureren (optioneel)

---

## 🚨 **SECURITY NOTES**

### **Wat NOOIT in code**
- Database passwords
- JWT secrets
- SMTP passwords
- Service role keys

### **Wat WEL public mag**
- Supabase URL
- Supabase anon key
- API base URL
- Public configuration

### **Best Practices**
- Gebruik verschillende secrets per environment
- Roteer secrets regelmatig
- Monitor API usage in Supabase dashboard
- Beperk CORS origins tot bekende domeinen

---

## 🔄 **TESTING ENDPOINTS**

### **Backend Health Check**
```bash
curl https://mail-saas-rf4s.onrender.com/api/v1/health
```

### **Frontend API Connection**
```bash
# Test vanuit browser console op https://mail-saas-xi.vercel.app
fetch('/api/v1/health').then(r => r.json()).then(console.log)
```

### **Database Connection**
```bash
# Test database via backend
curl https://mail-saas-rf4s.onrender.com/api/v1/leads
```

---

## 📞 **SUPPORT LINKS**

- **Supabase Dashboard**: https://supabase.com/dashboard/project/zpnklihryhpkaiyubkfn
- **Render Dashboard**: https://dashboard.render.com/web/srv-d3d76oggjchc739pgfn0
- **Vercel Dashboard**: https://vercel.com/punthelder-admins-projects/mail-saas
- **GitHub Repo**: https://github.com/basoffr/mail-saas

---

*Laatste update: 29 september 2025*
