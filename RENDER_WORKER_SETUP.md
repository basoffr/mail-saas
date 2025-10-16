# 🚀 RENDER WORKER SETUP - CRITICAL FOR CAMPAIGN LAUNCH

## ⚠️ **ZONDER DEZE WORKER START DE CAMPAGNE NIET!**

De `campaign_worker` is verantwoordelijk voor:
1. ✅ Activeren van scheduled campaigns (draft → active)
2. ✅ Versturen van messages op scheduled tijd
3. ✅ Completen van finished campaigns (active → completed)
4. ✅ Opslaan van alle statistics (events, opens, bounces)

---

## 📋 **SETUP INSTRUCTIES - RENDER.COM**

### **Optie A: Via Render Dashboard (Aanbevolen)**

1. **Ga naar Render Dashboard:**
   - https://dashboard.render.com/
   - Select je project: "Mail dashboard"

2. **Create New Background Worker:**
   - Click **"New +"** → **"Background Worker"**
   - Name: `mail-saas-worker`
   - Environment: `Python 3`
   - Region: `Frankfurt (EU Central)`

3. **Configure Worker:**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: python worker.py
   ```

4. **Environment Variables:**
   - Kopieer ALLE environment variables van je web service
   - Zelfde database URL, SMTP credentials, etc.
   - **KRITIEK:** Moet toegang hebben tot zelfde Supabase database!

5. **Instance Type:**
   - Starter: `$7/month` (voldoende voor 2103 leads)
   - Auto-deploy: `Enabled`

6. **Deploy:**
   - Click **"Create Background Worker"**
   - Wait for deployment (~2 minutes)

---

### **Optie B: Via render.yaml (Alternatief)**

Als je een `render.yaml` hebt, voeg dit toe:

```yaml
services:
  - type: web
    name: mail-saas-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    # ... existing config ...

  # ADD THIS:
  - type: worker
    name: mail-saas-worker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python worker.py
    envVars:
      # Copy all your existing env vars here
      - key: DATABASE_URL
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      # ... etc ...
```

---

## ✅ **VERIFICATIE**

### **1. Check Worker Logs:**
```
Render Dashboard → mail-saas-worker → Logs

Je zou moeten zien:
🚀 Starting Campaign Worker...
⏰ Worker will check every 60 seconds
📧 Campaigns will be activated and messages sent automatically
📊 Worker run at 2025-10-17 07:55:00+01:00
```

### **2. Check Campaign Activation:**
Morgen om 08:00 CET:
```
Logs:
🚀 Activated campaign 975e6e68-7af7-46dc-903f-26576a6ebd92: Webshop Campagin Version 1
✅ Activated 1 scheduled campaign(s)
Processing 2 messages for punthelder-vindbaarheid.nl
✅ Message sent successfully to lead@example.com
```

### **3. Check Database Status:**
```sql
-- Campaign should be active after 08:00
SELECT status FROM campaigns 
WHERE id = '975e6e68-7af7-46dc-903f-26576a6ebd92';
-- Expected: 'active'

-- Messages should start getting sent
SELECT status, COUNT(*) 
FROM messages 
WHERE campaign_id = '975e6e68-7af7-46dc-903f-26576a6ebd92'
GROUP BY status;
-- Expected: some 'sent', rest 'queued'
```

---

## 🔥 **EMERGENCY: Start Worker Locally (Backup)**

Als Render worker niet werkt, draai lokaal:

```powershell
cd "C:\Users\basof\OneDrive\Documenten\Punthelder\Mail dashboard\backend"
python worker.py
```

**⚠️ BELANGRIJK:** Moet blijven draaien! Open PowerShell moet open blijven.

---

## 📊 **WORKER BEHAVIOR**

### **Timing:**
- Checkt elke **60 seconden** (1 minute)
- Activeert campaigns als `start_at <= current_time`
- Stuurt messages als `scheduled_at <= current_time` AND within sending window

### **Sending Window:**
- **08:00 - 17:00** CET (werkdagen)
- **20 minuten** tussen emails per domein
- **4 domeinen parallel** (punthelder-vindbaarheid, -seo, -marketing, -zoekmachine)

### **Statistics Tracking:**
Automatisch opgeslagen:
- ✅ `sent` event bij succesvolle verzending
- ✅ `opened` event bij email open (tracking pixel)
- ✅ `bounced` event bij bounce
- ✅ `failed` event bij SMTP error

---

## 🎯 **EXPECTED TIMELINE - MORGEN**

```
08:00 CET - Worker activates campaign (draft → active)
08:00 CET - First message sent (Stream A, vindbaarheid domain)
08:10 CET - Second message sent (Stream B, seo domain)
08:20 CET - Third message sent (Stream A, marketing domain)
08:30 CET - Fourth message sent (Stream B, zoekmachine domain)
08:40 CET - Fifth message sent (Stream A, vindbaarheid domain)
...
17:00 CET - Sending window closes
Next day 08:00 - Continues sending remaining messages
```

**Totaal:** 2103 leads × 4 mails = 8,412 messages
**Throughput:** ~12 mails/hour = ~701 hours = ~29 dagen (~6 weken)

---

## 🚨 **TROUBLESHOOTING**

### **Worker niet gestart:**
```
Error: ModuleNotFoundError: No module named 'app'

Fix: Check dat Build Command correct is:
pip install -r requirements.txt
```

### **Database connection errors:**
```
Error: could not connect to server

Fix: Check DATABASE_URL environment variable
Moet zelfde zijn als web service!
```

### **No campaigns activated:**
```
Debug: Check start_at tijd in database
SELECT start_at FROM campaigns WHERE status = 'draft';

Moet in het verleden zijn om geactiveerd te worden!
```

---

## ✅ **CHECKLIST VOOR LAUNCH MORGEN:**

```
☐ Worker deployed on Render.com
☐ Worker logs show "Starting Campaign Worker..."
☐ Campaign start_at = 2025-10-17 08:00:00 CET ✅ (FIXED!)
☐ Campaign status = 'draft' ✅
☐ 8,412 messages created and queued ✅
☐ SMTP credentials configured in worker env vars
☐ Database URL configured in worker env vars
☐ Tracking pixel enabled (optional)
☐ Morning alarm set to check at 08:05 CET! 😅
```

**🚀 READY FOR LAUNCH!** (na worker deployment)
