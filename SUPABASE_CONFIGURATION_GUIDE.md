# 🗄️ SUPABASE CONFIGURATION GUIDE - COMPLETE SETUP

**Project**: Mail Dashboard - Mail SaaS Platform  
**Database**: PostgreSQL via Supabase  
**Status**: Complete configuration voor productie deployment  
**Datum**: 4 oktober 2025

---

## 📋 EXECUTIVE SUMMARY

Dit document bevat **alle Supabase configuratie** die nodig is om de database volledig op te zetten:

- ✅ **11 Database Tables** - Complete schema met alle relaties
- ✅ **60+ Indexes** - Performance optimization voor alle queries
- ✅ **RLS Policies** - Row Level Security voor multi-tenant support (future)
- ✅ **15+ Database Functions** - Business logic in SQL
- ✅ **8 Database Views** - Denormalized data voor performance
- ✅ **Triggers** - Auto-update timestamps, audit logs
- ✅ **Foreign Key Constraints** - Data integrity
- ✅ **Check Constraints** - Business rules enforcement

---

## 📁 CONFIGURATIE BESTANDEN

Alle SQL configuratie is opgesplitst in aparte bestanden:

1. **`supabase_schema.sql`** - Complete table definitions (11 tables)
2. **`supabase_indexes.sql`** - Performance indexes (60+ indexes)
3. **`supabase_rls.sql`** - Row Level Security policies
4. **`supabase_functions.sql`** - Database functions & stored procedures
5. **`supabase_views.sql`** - Denormalized views voor reporting
6. **`supabase_triggers.sql`** - Auto-update triggers

---

## 🗂️ DATABASE TABELLEN OVERZICHT

### **Core Modules (11 Tables)**

#### 1. **Leads Module** (3 tables)
- `leads` - Lead informatie met email, company, vars, status
- `assets` - Dashboard images en andere files
- `import_jobs` - Excel import tracking

#### 2. **Campaigns Module** (4 tables)
- `campaigns` - Campaign metadata en settings
- `campaign_audience` - Doelgroep selectie snapshot
- `messages` - Individuele emails per lead (4 mails per flow)
- `message_events` - Tracking events (sent, opened, bounced)

#### 3. **Templates Module** (1 table)
- `templates` - Email templates met subject/body/vars

#### 4. **Reports Module** (2 tables)
- `reports` - Uploaded PDF/Excel/Image files
- `report_links` - Many-to-many koppeling met leads/campaigns

#### 5. **Inbox Module** (3 tables)
- `mail_accounts` - IMAP account configuratie
- `mail_messages` - Received emails met smart linking
- `mail_fetch_runs` - IMAP fetch job tracking

#### 6. **Settings Module** (1 table)
- `settings` - Singleton configuratie tabel

---

## 🚀 DEPLOYMENT VOLGORDE

### **Stap 1: Basis Schema** (5 min)
```bash
# Run in Supabase SQL Editor
psql -h [DB_HOST] -U postgres -d postgres < supabase_schema.sql
```

### **Stap 2: Indexes** (10 min)
```bash
# Performance indexes - kan CONCURRENTLY voor zero downtime
psql -h [DB_HOST] -U postgres -d postgres < supabase_indexes.sql
```

### **Stap 3: Views** (2 min)
```bash
# Denormalized views voor reporting
psql -h [DB_HOST] -U postgres -d postgres < supabase_views.sql
```

### **Stap 4: Functions** (3 min)
```bash
# Business logic functies
psql -h [DB_HOST] -U postgres -d postgres < supabase_functions.sql
```

### **Stap 5: Triggers** (2 min)
```bash
# Auto-update triggers
psql -h [DB_HOST] -U postgres -d postgres < supabase_triggers.sql
```

### **Stap 6: RLS Policies** (5 min - OPTIONEEL)
```bash
# Row Level Security - alleen voor multi-tenant
psql -h [DB_HOST] -U postgres -d postgres < supabase_rls.sql
```

**Totale deployment tijd**: ~30 minuten

---

## 🔑 KRITIEKE CONFIGURATIE ITEMS

### **A. Foreign Key Constraints**
Alle relaties hebben foreign keys met `ON DELETE CASCADE`:
- ✅ `messages.campaign_id` → `campaigns.id`
- ✅ `messages.lead_id` → `leads.id`
- ✅ `report_links.report_id` → `reports.id`
- ✅ `mail_messages.account_id` → `mail_accounts.id`
- ✅ Alle andere relaties

### **B. Unique Constraints**
Business rules enforcement:
- ✅ `leads.email` - Één lead per email
- ✅ `messages.smtp_message_id` - Unieke SMTP tracking
- ✅ `messages(campaign_id, lead_id)` - Één message per campaign-lead combi
- ✅ `assets.key` - Unieke asset keys

### **C. Check Constraints**
Data validation in database:
- ✅ `campaigns.status` IN ('draft', 'running', 'paused', 'completed', 'stopped')
- ✅ `messages.status` IN ('queued', 'sent', 'bounced', 'opened', 'failed', 'canceled')
- ✅ `messages.mail_number` BETWEEN 1 AND 4
- ✅ `leads.status` IN ('active', 'suppressed', 'bounced')
- ✅ `report_links` - Exact één van (lead_id, campaign_id) must be set

### **D. Critical Indexes**
Performance-critical indexes:
- ✅ `idx_leads_email` - Unique index voor lead lookup
- ✅ `idx_messages_scheduled_at` - Voor campaign scheduler
- ✅ `idx_messages_status_scheduled` - Composite voor queue queries
- ✅ `idx_leads_active_targeting` - Voor audience selection
- ✅ `idx_mail_messages_message_id` - Voor inbox linking

---

## 📊 DATABASE VIEWS

### **1. leads_enriched**
Complete lead view met alle computed fields:
```sql
SELECT 
    l.*,
    EXISTS(SELECT 1 FROM report_links WHERE lead_id = l.id) as has_report,
    (l.image_key IS NOT NULL AND l.image_key != '') as has_image,
    -- vars completeness calculation
FROM leads l
WHERE l.deleted_at IS NULL;
```

### **2. campaign_kpis**
Real-time campaign statistics:
```sql
SELECT 
    c.id,
    c.name,
    COUNT(m.id) as total_planned,
    COUNT(CASE WHEN m.status = 'sent' THEN 1 END) as total_sent,
    COUNT(CASE WHEN m.status = 'opened' THEN 1 END) as total_opened,
    -- open_rate, click_rate, etc.
FROM campaigns c
LEFT JOIN messages m ON c.id = m.campaign_id
GROUP BY c.id;
```

### **3. message_timeline**
Daily aggregated message stats per campaign:
```sql
SELECT 
    campaign_id,
    DATE(sent_at) as date,
    COUNT(*) as sent,
    COUNT(CASE WHEN status = 'opened' THEN 1 END) as opened
FROM messages
GROUP BY campaign_id, DATE(sent_at);
```

---

## 🔐 ROW LEVEL SECURITY (RLS)

### **Huidige Status: DISABLED**
RLS is **niet actief** in MVP omdat we single-tenant zijn.

### **Future Multi-Tenant Setup**
Voor multi-tenant support, enable RLS op alle tabellen:

```sql
-- Enable RLS op alle tabellen
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
-- etc.

-- Policy: Users kunnen alleen eigen data zien
CREATE POLICY leads_tenant_isolation ON leads
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

**Opmerking**: Voor MVP is dit NIET nodig. Implementeer alleen bij multi-tenant vereiste.

---

## ⚡ PERFORMANCE OPTIMALISATIE

### **Query Performance Targets**
- ✅ Lead list query: **< 100ms** (met pagination)
- ✅ Campaign KPIs: **< 200ms** (via views)
- ✅ Message scheduling: **< 50ms** per message
- ✅ Inbox linking: **< 100ms** per message

### **Index Strategy**
1. **Single-column indexes**: Voor eenvoudige filters (status, email, domain)
2. **Composite indexes**: Voor complexe queries (status + scheduled_at)
3. **Partial indexes**: Voor hot queries (alleen active records)
4. **GIN indexes**: Voor JSON columns (vars, meta)

### **Connection Pooling**
```python
# FastAPI settings
SQLALCHEMY_DATABASE_URL = "postgresql://user:pass@host/db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,  # Voor Render Free tier
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

## 🧪 VALIDATIE & TESTING

### **Post-Deployment Checklist**

#### 1. Schema Validatie
```sql
-- Check alle tabellen bestaan
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
-- Verwacht: 11 tables

-- Check alle indexes
SELECT tablename, indexname FROM pg_indexes 
WHERE schemaname = 'public';
-- Verwacht: 60+ indexes
```

#### 2. Constraint Validatie
```sql
-- Check foreign keys
SELECT constraint_name, table_name 
FROM information_schema.table_constraints 
WHERE constraint_type = 'FOREIGN KEY';
-- Verwacht: 15+ foreign keys

-- Check unique constraints
SELECT constraint_name, table_name 
FROM information_schema.table_constraints 
WHERE constraint_type = 'UNIQUE';
-- Verwacht: 5+ unique constraints
```

#### 3. View Validatie
```sql
-- Check views bestaan
SELECT table_name FROM information_schema.views 
WHERE table_schema = 'public';
-- Verwacht: 8 views

-- Test view query
SELECT * FROM leads_enriched LIMIT 1;
SELECT * FROM campaign_kpis LIMIT 1;
```

#### 4. Performance Test
```sql
-- Test lead query performance
EXPLAIN ANALYZE 
SELECT * FROM leads 
WHERE status = 'active' 
  AND deleted_at IS NULL 
LIMIT 20;
-- Verwacht: < 100ms

-- Test campaign KPI performance
EXPLAIN ANALYZE 
SELECT * FROM campaign_kpis WHERE id = 'test-campaign-id';
-- Verwacht: < 200ms
```

---

## 🔄 DATA MIGRATIE (In-Memory → PostgreSQL)

### **Migratie Strategy**

#### **Optie 1: Fresh Start** (AANBEVOLEN voor MVP)
```python
# Lege database, start met seed data
python scripts/seed_database.py
```

#### **Optie 2: Export/Import** (voor bestaande data)
```python
# 1. Export in-memory data naar JSON
python scripts/export_inmemory_data.py

# 2. Import JSON naar PostgreSQL
python scripts/import_to_postgres.py
```

### **Seed Data Requirements**
- ✅ 16 Templates (v1m1-v4m4) - zie `templates_store.py`
- ✅ Settings singleton met 4 domains
- ✅ 8 Mail accounts (2 per domain: christian@ + victor@)
- ⚠️ GEEN sample leads/campaigns (clean start)

---

## 📝 ENVIRONMENT VARIABLES

### **Backend .env Updates**
```bash
# Supabase Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_KEY=[ANON_KEY]
SUPABASE_SERVICE_KEY=[SERVICE_ROLE_KEY]

# Disable in-memory stores
USE_IN_MEMORY_STORES=false  # Switch to PostgreSQL

# Connection pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
```

### **Supabase Dashboard Settings**
1. **Database Settings**
   - Connection pooling: **Enabled** (Transaction mode)
   - Statement timeout: **30s**
   - Max connections: **50** (adjust per plan)

2. **Storage Settings**
   - Bucket: `reports` (voor PDF/Excel files)
   - Bucket: `assets` (voor dashboard images)
   - Max file size: **10MB** per file

3. **API Settings**
   - JWT expiry: **1 hour**
   - Max rows: **1000** (voor API responses)

---

## 🎯 PRODUCTION READINESS CHECKLIST

### **Database Configuration** ✅
- [x] Alle 11 tabellen gedefinieerd
- [x] 60+ indexes voor performance
- [x] Foreign key constraints
- [x] Unique constraints
- [x] Check constraints
- [x] 8 database views
- [x] Triggers voor auto-update

### **Security** ⚠️
- [ ] RLS policies (alleen bij multi-tenant)
- [x] JWT authentication (via Supabase)
- [x] API key security
- [ ] SSL enforcement (Supabase default)

### **Performance** ✅
- [x] Query optimization via indexes
- [x] Connection pooling configuratie
- [x] View denormalization
- [ ] Query monitoring (via Supabase dashboard)

### **Monitoring** ⚠️
- [ ] Supabase dashboard monitoring
- [ ] Query performance tracking
- [ ] Slow query alerts
- [ ] Database size monitoring

---

## 📞 NEXT STEPS

### **Immediate Actions** (Week 1)
1. ✅ Run `supabase_schema.sql` - Deploy alle tabellen
2. ✅ Run `supabase_indexes.sql` - Deploy indexes
3. ✅ Run `supabase_views.sql` - Deploy views
4. ✅ Run `supabase_functions.sql` - Deploy functions
5. ✅ Run `supabase_triggers.sql` - Deploy triggers
6. ✅ Seed templates en settings data
7. ✅ Update backend .env met DATABASE_URL
8. ✅ Test backend connectivity
9. ✅ Validate schema met checklist hierboven

### **Follow-up** (Week 2)
10. ⚠️ Performance monitoring setup
11. ⚠️ Backup strategy configuratie
12. ⚠️ Query optimization based on real usage
13. ⚠️ RLS policies (alleen als multi-tenant nodig is)

---

## 🔗 REFERENTIES

- **DB Check Reports**: `LEADS_DB_CHECK.md`, `CAMPAIGNS_DB_CHECK.md`, `REPORTS_DB_CHECK.md`
- **Backend Models**: `backend/app/models/*.py`
- **SQL Scripts**: Zie de 6 aparte SQL bestanden
- **Supabase Docs**: https://supabase.com/docs/guides/database

---

**Status**: 📋 CONFIGURATIE COMPLEET  
**Deployment Ready**: ✅ YES  
**Geschat deployment tijd**: 30 minuten
