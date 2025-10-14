# Migration Scripts

## Reports Migration Script

Migreert reports van Supabase Storage naar de database table.

### Prerequisites

```bash
# Environment variables in .env file:
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Usage

**1. Dry Run (test zonder wijzigingen):**
```bash
python scripts/migrate_reports_to_db.py --dry-run
```

**2. Live Migration:**
```bash
python scripts/migrate_reports_to_db.py
```

**3. Only Auto-Link (als reports al gemigreerd zijn):**
```bash
python scripts/migrate_reports_to_db.py --link-only
```

### Wat doet het script?

1. **List Files**: Haalt alle files uit Supabase Storage bucket `reports/`
2. **Check Existing**: Controleert welke reports al in database zitten (voorkomt duplicates)
3. **Migrate**: Maakt `reports` table records aan voor elk bestand
4. **Auto-Link**: Linkt reports automatisch aan leads op basis van domain matching

### Auto-Linking Logic

Het script probeert automatisch reports te linken aan leads:

```
Filename: example.com_report.pdf
→ Extract domain: "example.com"
→ Find lead with domain = "example.com"
→ Create report_link entry
```

Filename patterns:
- `example.com_report.pdf` → domain: `example.com`
- `www.example.nl_seo.pdf` → domain: `example.nl`
- `domain-name_file.pdf` → domain: `domain-name`

### Output

```
🚀 Starting reports migration...
Mode: LIVE MIGRATION

📁 Step 1: Listing files in 'reports' bucket...
Found 2103 files in storage

📊 Step 2: Checking existing reports in database...
Found 0 existing reports in database

🔄 Step 3: Migrating reports to database...
✅ Migrated: example.com_report.pdf (domain: example.com)
✅ Migrated: test.nl_seo.pdf (domain: test.nl)
...

==============================================================
📊 MIGRATION SUMMARY
==============================================================
Total files in storage: 2103
Already in database:    0
Migrated:               2103
Failed:                 0
==============================================================

🔗 Step 4: Auto-linking reports to leads...
🔗 Linked: example.com_report.pdf → lead (domain: example.com)
...
✅ Auto-linked 2103 reports to leads

✅ Migration completed!
```

### Troubleshooting

**Error: "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required"**
- Zorg dat environment variables correct zijn in `.env` file
- Run: `source .env` (Linux/Mac) of laad .env in PowerShell

**Error: "Failed to list files"**
- Check Supabase Storage bucket naam (moet `reports` zijn)
- Check bucket permissions (service role moet read access hebben)

**Reports niet gelinkt aan leads**
- Run: `python scripts/migrate_reports_to_db.py --link-only`
- Check of lead domains overeenkomen met filename patterns
- Check logs voor domain extraction details

### Manual Cleanup (indien nodig)

```sql
-- Delete all migrated reports (rollback)
DELETE FROM report_links WHERE report_id IN (
  SELECT id FROM reports WHERE meta->>'migrated_from_storage' = 'true'
);
DELETE FROM reports WHERE meta->>'migrated_from_storage' = 'true';
```

### Next Steps

Na succesvolle migratie:
1. Check Reports page in frontend → Zou nu 2103 reports moeten tonen
2. Test search functionaliteit (domain/email search)
3. Test download/view functionaliteit
4. Verifieer report links (Bound To kolom)
