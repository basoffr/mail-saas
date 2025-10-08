# 🎯 Campaign Audience Setup Guide

## Problem Solved
**Issue:** Campaigns showed 0 leads when using list name "Webshop Campaign V1"  
**Cause:** No audience filtering logic based on list_name + eligibility criteria  
**Solution:** New `/admin/audience-by-list` endpoint + proper filtering

---

## 📋 How Campaign Audience Works

### Lead Eligibility Criteria
For a lead to be included in a campaign audience, it must meet ALL these requirements:

1. ✅ **List Membership:** `list_name` matches the target list
2. ✅ **Status:** `status = 'active'` (not suppressed/bounced)
3. ✅ **Not Stopped:** `stopped = false`
4. ✅ **Not Deleted:** `deleted_at IS NULL`
5. ✅ **Has Report:** `vars->>'report_filename' IS NOT NULL`
6. ✅ **Has Image:** `image_key IS NOT NULL`

**Example:**
```
"Webshop Campaign V1" list: 2103 total leads
After filters: ~2094-2103 eligible leads (depends on stopped/deleted status)
```

---

## 🔧 New Admin Endpoints

### 1. Get Audience by List Name
```
GET /api/v1/admin/audience-by-list?list_name=Webshop%20Campaign%20V1
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": {
    "list_name": "Webshop Campaign V1",
    "total_in_list": 2103,
    "eligible_count": 2094,
    "lead_ids": ["uuid1", "uuid2", ...],
    "filters_applied": {
      "status": "active",
      "stopped": false,
      "deleted": false,
      "has_report": true,
      "has_image": true
    }
  },
  "error": null
}
```

### 2. List All List Names
```
GET /api/v1/admin/list-names
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": ["Webshop Campaign V1", "Other List", ...],
  "error": null
}
```

---

## 🚀 Usage in Campaign Creation

### Frontend Integration
When creating a campaign, the frontend should:

1. **Get available lists:**
   ```javascript
   const { data } = await fetch('/api/v1/admin/list-names');
   // Show dropdown with list names
   ```

2. **Get audience for selected list:**
   ```javascript
   const list_name = "Webshop Campaign V1";
   const { data } = await fetch(
     `/api/v1/admin/audience-by-list?list_name=${encodeURIComponent(list_name)}`
   );
   
   const lead_ids = data.lead_ids; // Use in campaign creation
   const audience_count = data.eligible_count; // Show to user
   ```

3. **Create campaign with audience:**
   ```javascript
   await fetch('/api/v1/campaigns', {
     method: 'POST',
     body: JSON.stringify({
       name: "My Campaign",
       template_id: "...",
       domain: "...",
       audience: {
         lead_ids: lead_ids, // From step 2
         exclude_suppressed: true,
         exclude_recent_days: 7,
         one_per_domain: true
       },
       schedule: { ... }
     })
   });
   ```

---

## 📊 Database Schema

### Leads Table
```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  domain TEXT,
  status TEXT DEFAULT 'active',
  list_name TEXT,  -- Links lead to list!
  image_key TEXT,  -- Screenshot path
  vars JSONB,      -- Contains report_filename
  stopped BOOLEAN DEFAULT false,
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);

CREATE INDEX idx_leads_list_name ON leads(list_name);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_stopped ON leads(stopped);
CREATE INDEX idx_leads_deleted_at ON leads(deleted_at);
```

### Campaign Audience (In-Memory)
```python
class CampaignAudience:
    id: str
    campaign_id: str
    lead_ids: List[str]  # Filtered lead IDs!
    exclude_suppressed: bool
    exclude_recent_days: int
    one_per_domain: bool
```

---

## 🔍 Debugging

### Check Lead Eligibility
```javascript
// Get all leads from list
const allLeads = await fetch('/api/v1/leads?list_name=Webshop%20Campaign%20V1&page_size=100');

// Check individual lead
const lead = allLeads.data.items[0];
console.log({
  email: lead.email,
  status: lead.status,           // Should be 'active'
  stopped: lead.stopped,         // Should be false
  deleted: lead.deletedAt,       // Should be null
  hasImage: lead.hasImage,       // Should be true
  hasReport: lead.hasReport,     // Should be true
  image_key: lead.imageKey,
  report: lead.vars?.report_filename
});
```

### Test Audience Endpoint
```bash
# Get audience
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://mail-saas-rf4s.onrender.com/api/v1/admin/audience-by-list?list_name=Webshop%20Campaign%20V1"

# Should return ~2094+ lead IDs
```

---

## 🎯 Common Issues

### Issue: 0 leads returned
**Causes:**
1. ❌ Wrong list_name (typo, case-sensitive)
2. ❌ All leads are stopped/deleted
3. ❌ Missing reports/images

**Solution:**
```javascript
// Check list names
const lists = await fetch('/api/v1/admin/list-names');
console.log('Available lists:', lists.data);

// Check audience with actual list name
const audience = await fetch(
  `/api/v1/admin/audience-by-list?list_name=${lists.data[0]}`
);
console.log('Eligible leads:', audience.data.eligible_count);
```

### Issue: Fewer leads than expected
**Causes:**
1. ✅ Filters working correctly (some leads don't meet criteria)
2. ❌ Some leads missing images/reports

**Solution:**
```sql
-- Check why leads are filtered out
SELECT 
  COUNT(*) FILTER (WHERE status != 'active') as not_active,
  COUNT(*) FILTER (WHERE stopped = true) as stopped,
  COUNT(*) FILTER (WHERE deleted_at IS NOT NULL) as deleted,
  COUNT(*) FILTER (WHERE image_key IS NULL) as no_image,
  COUNT(*) FILTER (WHERE vars->>'report_filename' IS NULL) as no_report
FROM leads
WHERE list_name = 'Webshop Campaign V1';
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] GET `/api/v1/admin/list-names` returns list names
- [ ] GET `/api/v1/admin/audience-by-list?list_name=...` returns lead IDs
- [ ] `eligible_count` matches expected number (~2094+)
- [ ] Campaign creation uses `lead_ids` from audience endpoint
- [ ] Frontend shows correct audience count before sending campaign

---

## 🚀 Production Ready

**Changes made:**
1. ✅ New `admin.py` API router with 2 endpoints
2. ✅ Registered in `main.py`
3. ✅ Uses existing `leads_store.query()` with proper filters
4. ✅ Auth required (JWT token)
5. ✅ Clean error handling + logging
6. ✅ Campaign router now registered in main.py (was missing!)

**No breaking changes** - existing functionality preserved!
