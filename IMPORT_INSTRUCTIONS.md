# 📦 DATA IMPORT INSTRUCTIES

## 🎯 Overzicht

Import script voor **2.134 leads** + **2.132 PDF reports** naar Supabase.

**Wat wordt geïmporteerd:**
- ✅ 2.134 leads van Excel → `leads` table
- ✅ 2.132 PDF reports → Supabase Storage `reports` bucket + `reports` table  
- ✅ Auto-linking reports ↔ leads via `report_links` table
- ⏳ Screenshots (handmatig na ZIP extractie)

---

## 🚀 Stap-voor-stap

### **STAP 1: Storage Buckets Aanmaken**

**Run dit in Supabase SQL Editor:**

```bash
# Open file:
supabase_create_storage_buckets.sql
```

Kopieer en run de hele file in Supabase SQL Editor. Dit maakt:
- `reports` bucket (private, 50MB limit, PDFs)
- `assets` bucket (public, 10MB limit, images)
- Storage policies voor authenticated users

**Verwachte output:**
```
✅ 2 buckets created
✅ 8 storage policies created
```

---

### **STAP 2: Python Dependencies Installeren**

```powershell
# Install requirements
pip install -r requirements_import.txt
```

**Geïnstalleerd:**
- `supabase` - Supabase Python client
- `pandas` - Excel processing
- `tqdm` - Progress bars
- `openpyxl` - Excel reader

---

### **STAP 3: Import Script Runnen**

```powershell
# Run import
python import_data_to_supabase.py
```

**Verwachte duur:** ~10-15 minuten

**Progress output:**
```
=================================================================
🚀 SUPABASE DATA IMPORT
=================================================================

📊 STEP 1: Importing Leads from Excel...
   Found 2134 leads in Excel
Importing leads: 100%|████████████| 22/22 [00:15<00:00]
✅ Imported 2134 leads

📄 STEP 2: Uploading PDF Reports...
   Found 2132 PDF files
Uploading reports: 100%|████████████| 2132/2132 [08:45<00:00]
✅ Uploaded 2132 reports

🔗 STEP 3: Linking Reports to Leads...
Creating links: 100%|████████████| 2134/2134 [00:23<00:00]
✅ Created 1856 report-lead links

📸 STEP 4: Screenshots Import...
⚠️  Screenshot import requires manual ZIP extraction first

=================================================================
📊 IMPORT COMPLETE
=================================================================
✅ Leads imported:     2134
⚠️  Leads skipped:     0
✅ Reports uploaded:   2132
⚠️  Reports failed:    0
✅ Links created:      1856

⏱️  Total time: 627.3 seconds
=================================================================
```

---

## 🔍 Verificatie

**Check in Supabase:**

```sql
-- Check leads
SELECT COUNT(*) as total_leads FROM leads;
-- Expected: 2134

-- Check reports
SELECT COUNT(*) as total_reports FROM reports;
-- Expected: 2132

-- Check links
SELECT COUNT(*) as total_links FROM report_links;
-- Expected: ~1850-1900 (auto-matched)

-- Check storage
SELECT bucket_id, COUNT(*) as files, SUM(metadata->>'size')::bigint / 1024 / 1024 as total_mb
FROM storage.objects
GROUP BY bucket_id;
-- Expected: reports bucket ~740MB
```

---

## 📸 Screenshots Import (STAP 4)

**Handmatige stappen:**

1. **Extract ZIP:**
   ```powershell
   # Extract screenshots.zip to:
   Importable data\screenshots\
   ```

2. **Update script:**
   - Open `import_data_to_supabase.py`
   - Find function `import_screenshots_placeholder()`
   - Uncomment implementation
   - Run: `python import_data_to_supabase.py --screenshots-only`

3. **Auto-matching:**
   - Script matched screenshot filenames met lead URLs
   - Updates `leads.image_key` met asset reference

---

## ⚠️ Troubleshooting

**Error: "bucket does not exist"**
- ✅ Run `supabase_create_storage_buckets.sql` eerst

**Error: "duplicate key value violates unique constraint"**
- ✅ Normale bij re-runs, leads met duplicate emails worden geskipt

**Error: "authentication required"**
- ✅ Check `SUPABASE_KEY` in script (moet anon key zijn)

**Error: "file too large"**
- ✅ Check bucket limits (50MB reports, 10MB assets)

**Slow upload speeds?**
- ✅ Normale voor 2132 files, ~740MB data
- ✅ Supabase free tier bandwidth: ~50GB/maand
- ✅ Expected speed: ~1-2MB/sec = ~10 min total

---

## 📊 Data Mapping

**Excel → Database:**
```
email         → leads.email
company       → leads.company
url           → leads.url
domain        → leads.domain (extracted)
keyword       → leads.vars->>'keyword'
google_rank   → leads.vars->>'google_rank'
seo_score     → leads.vars->>'seo_score'
```

**PDF Filename → Report Matching:**
```
sans-online_nl_report.pdf → lead with URL "https://www.sans-online.nl/"
Domain extraction → Auto-link via report_links table
```

---

## ✅ Completion Checklist

- [ ] Storage buckets aangemaakt (SQL script)
- [ ] Dependencies geïnstalleerd (pip install)
- [ ] Import script gerund (python script)
- [ ] Leads verified (2134 in database)
- [ ] Reports verified (2132 in storage)
- [ ] Links verified (~1850 in report_links)
- [ ] Screenshots extracted (manual)
- [ ] Screenshots uploaded (optional step)

---

## 🎉 Klaar!

Na deze import heb je:
- ✅ **2.134 leads** ready voor campaigns
- ✅ **2.132 reports** gekoppeld aan leads
- ✅ **Database 100% gevuld** voor production use

**Next steps:**
- Test frontend lead filtering
- Test report preview links
- Run first campaign!
