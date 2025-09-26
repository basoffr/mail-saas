# 🌐 API – Private Mail SaaS

## 📌 Conventies
- **Base URL**: `/api/v1`
- **Auth**: Bearer token (Supabase JWT).
- **Response shape**: `{ data: ..., error: null }` of `{ data: null, error: "message" }`
- **Tijdzone**: Europe/Amsterdam
- **Content-Type**: `application/json` tenzij file upload.

---

## 🧾 Leads
### GET `/leads`
Query params:
- `page`, `page_size`
- Filters: `status`, `domain_tld`, `has_image`, `has_var`

Response:
```json
{ "data": { "items": [Lead], "total": 123 }, "error": null }
```

### GET `/leads/{id}`
Response: `{ "data": Lead, "error": null }`

### POST `/import/leads`
Multipart file upload (.xlsx/.csv).
Response:
```json
{ "data": { "inserted": 2100, "updated": 50, "skipped": 20, "jobId": "uuid" }, "error": null }
```

### GET `/assets/image-by-key?key=...`
Response: `{ "data": { "url": "https://..." }, "error": null }`

---

## 📣 Campaigns
### GET `/campaigns`
Response: `{ "data": { "items": [Campaign], "total": 5 }, "error": null }`

### POST `/campaigns`
Payload:
```json
{
  "name": "string",
  "template_id": "uuid",
  "audience": { "filter": {}, "lead_ids": [] },
  "schedule": { "start": "2025-09-25T08:00:00" },
  "domains": ["d1.com","d2.com"],
  "followup": { "enabled": true, "days": 3, "attach_report": true }
}
```
Response: `{ "data": { "id": "uuid" }, "error": null }`

### GET `/campaigns/{id}`
Response: `{ "data": CampaignDetail, "error": null }`

### POST `/campaigns/{id}/pause|resume|stop`
Response: `{ "data": { "ok": true }, "error": null }`

### POST `/campaigns/{id}/dry-run`
Response:
```json
{ "data": { "byDay": [{"date":"2025-09-25","planned":120}] }, "error": null }
```

---

## 📝 Templates
### GET `/templates`
Response: `{ "data": { "items": [Template] }, "error": null }`

### GET `/templates/{id}`
Response: `{ "data": Template, "error": null }`

### GET `/templates/{id}/preview?lead_id=...`
Response:
```json
{ "data": { "html": "...", "text": "...", "warnings": ["missing vars"] }, "error": null }
```

### POST `/templates/{id}/testsend`
Payload: `{ "to": "string", "leadId": "uuid" }`
Response: `{ "data": { "ok": true }, "error": null }`

---

## 📂 Reports
### GET `/reports`
Query params: filters (type, bound/unbound, date).
Response: `{ "data": { "items": [ReportItem], "total": 12 }, "error": null }`

### POST `/reports/upload`
Multipart file + optional `{lead_id|campaign_id}`.
Response: `{ "data": ReportItem, "error": null }`

### POST `/reports/bulk?mode=by_image_key|by_email`
ZIP upload.
Response: `{ "data": BulkUploadResult, "error": null }`

### POST `/reports/bind`
Payload: `{ report_id, lead_id|campaign_id }`
Response: `{ "data": { "ok": true }, "error": null }`

### POST `/reports/unbind`
Payload: `{ report_id }`
Response: `{ "data": { "ok": true }, "error": null }`

### GET `/reports/{id}/download`
Response: binary/URL.

---

## 📊 Stats
### GET `/stats/summary`
Response:
```json
{ "data": {
  "global": { "totalSent": 2100, "openRate": 0.45, "bounces": 23 },
  "domains": [ {"domain":"d1.com","sent":500,"openRate":0.5,"bounces":5} ],
  "campaigns": [ {"id":"uuid","name":"C1","sent":1000,"openRate":0.4,"bounces":10} ],
  "timeline": [ {"date":"2025-09-25","sent":200,"opens":50} ]
}, "error": null }
```

### GET `/stats/export?scope=global|domain|campaign`
Response: CSV file.

---

## ⚙️ Settings
### GET `/settings`
Response: `{ "data": Settings, "error": null }`

### POST `/settings`
Partial update.
Response: `{ "data": { "ok": true }, "error": null }`

---

## 📡 Tracking & Unsubscribe
### GET `/track/open.gif?m={message_id}&t={token}`
- Returns 1×1 gif.
- Side effect: logs open event.

### GET `/unsubscribe?m=...`
- Redirect naar unsubscribe page.

### POST `/unsubscribe`
Payload: `{ message_id, reason? }`
Response: `{ "data": { "ok": true }, "error": null }`

---
© 2025 – Private Mail SaaS