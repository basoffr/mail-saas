# 🔧 Windsurf Fix — Inbox/Settings (IMAP-accounts + domains)

**Scope (alleen dit wijzigen):**  
Backend: `models/mail.py`, `api/settings.py`, `services/inbox/*`, `seed/imap_accounts.py` (nieuw)  
Frontend: `pages/Inbox.tsx`, `pages/Settings.tsx`, `services/settings.ts` (klein), `services/inbox.ts` (optioneel)

---

## 0) Lees eerst
- `tab7_inbox_replies_implementatieplan.md`, `api.md`, `rules.md`
- `environment_variables_setup` (Render secrets: IMAP_*), `CONSOLELOGS_EVERY_TABv3.txt`

---

## 1) Backend

### 1.1 Model (check/aanvullen)
`MailAccount { id, label, imap_host, imap_port=993, use_ssl=true, username, secret_ref, active=true, last_fetch_at, last_seen_uid, created_at, updated_at }`  
- Unique index: `(username)` of `(imap_host, username)`

### 1.2 Seeder (nieuw) `seed/imap_accounts.py`
- **Idempotent upsert** 8 users × 4 domeinen op basis van env’s:  
  `IMAP_HOST_MARKETING|SEO|VINDBAARHEID|ZOEKMACHINE`  
  `IMAP_USER_*` en **secret_ref** = **exacte env key** `IMAP_PASSWORD_*`
- Zet `active=True`, `use_ssl=env(IMAP_USE_SSL,true)`, `imap_port=env(IMAP_PORT,993)`

### 1.3 Settings API
- `GET /settings/inbox/accounts` → **gemaskeerde** `username`, `host`, `port`, `active`, `last_fetch_at`, `last_seen_uid`
- `GET /settings` verrijken met:
  - `domains[]`: unieke domeinen (parse uit usernames) **+** bestaande lijst
  - Laat overige velden ongewijzigd
- **Geen** `secret_ref` of wachtwoord in responses

### 1.4 Fetch guard
- Respecteer `IMAP_FETCH_INTERVAL_MINUTES` (default 5) per account (server‑side guard)

---

## 2) Frontend

### 2.1 Settings
- Nieuwe sectie **“Actieve IMAP-accounts”** (compacte tabel): Kolommen `Account`, `Host`, `Port`, `Laatste fetch`, `Last UID`, `Status`
- Domeinenlijst tonen onder “Domeinen” (read‑only)

### 2.2 Inbox
- Als `accounts.length === 0` → warning (huidig gedrag)  
- Als `> 0` → info‑banner “Accounts geconfigureerd” en **filter dropdown** met accounts
- “Ophalen” button disabled tijdens fetch; toont toast bij error/success

---

## 3) Tests (kort)
- Seeder runt zonder duplicaten; 8 accounts aanwezig
- `GET /settings/inbox/accounts` maskeert usernames
- `GET /settings` bevat `domains[]` met 4 domeinen
- Inbox/Settings renderen zonder console‑errors met ≥1 account

---

## 4) Voorbeelddiffs

```diff
*** a/backend/api/settings.py
--- b/backend/api/settings.py
@@
 @router.get("/settings/inbox/accounts")
 def list_accounts():
-    ...
+    rows = db.query(MailAccount).filter(MailAccount.active==True).all()
+    def mask(u: str) -> str:
+        if not u or "@" not in u: return "•••"
+        name, dom = u.split("@",1)
+        return f"{name[:3]}…@{dom}"
+    data = [{
+        "label": r.label, "host": r.imap_host, "port": r.imap_port,
+        "username": mask(r.username), "active": r.active,
+        "last_fetch_at": r.last_fetch_at, "last_seen_uid": r.last_seen_uid,
+    } for r in rows]
+    return {"data": data, "error": None}
@@
 @router.get("/settings")
 def get_settings():
-    s = settings_service.get()
-    return {"data": s, "error": None}
+    s = settings_service.get()
+    accounts = db.query(MailAccount.username).filter(MailAccount.active==True).all()
+    domains = sorted({ (u[0].split("@",1)[1]) for u in accounts if u and "@" in u[0] })
+    s["domains"] = sorted(set(s.get("domains", [])) | set(domains))
+    return {"data": s, "error": None}
```

---

## 5) DoD
- Seeds aanwezig; `GET /settings/inbox/accounts` geeft lijst terug
- Settings toont accounts + 4 domeinen
- Inbox toont geen “Geen accounts” waarschuwing meer bij seeds
