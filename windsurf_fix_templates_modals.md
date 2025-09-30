# ✉️ Windsurf Fix — Templates (modals: Bekijken, Variabelen, Test)

**Scope (alleen dit wijzigen):**  
Backend: `api/templates.py`, `services/mailer.py`  
Frontend: `pages/Templates.tsx`, `components/templates/*` (3 modals), `services/templates.ts`

---

## 0) Lees eerst
- `tab2_templates_implementatieplan.md`, `api.md`, `rules.md`

---

## 1) Backend

### 1.1 Detail endpoint
- `GET /templates/{id}` → `{ id, name, subject, body_html, body_text, required_vars[] }`  
- Data komt uit de bestaande hard‑coded map

### 1.2 Testsend endpoint
- `POST /templates/{id}/testsend` body: `{ to?: string, leadId?: string }`  
- Default `to = "punthelderoutreach@gmail.com"` indien niet opgegeven
- Render met dummy lead als `leadId` ontbreekt
- Voeg **List-Unsubscribe** header toe en respecteer `trackingPixelEnabled` uit settings
- Response: `{ ok: true }` bij succes

---

## 2) Frontend

### 2.1 Lijstscherm
- Verwijder **Preview**‑knop
- Behoud **Bekijken**, **Variabelen**, **Test**

### 2.2 Modals (nieuw)
- `TemplateViewDialog.tsx`
  - Laadt `GET /templates/{id}` bij open
  - Tabs: **Inhoud (HTML)** + **Text** + **Meta**
- `TemplateVariablesDialog.tsx`
  - Toont `required_vars[]` (+ kopieerbare JSON met dummy‑values)
- `TemplateTestDialog.tsx`
  - Input “Verstuur naar” **readonly** = `punthelderoutreach@gmail.com`
  - Knop **Verstuur test** → `POST /templates/{id}/testsend` (disable tijdens request; success toast)

### 2.3 Services
- `getTemplate(id)`, `testsendTemplate(id, {to?, leadId?})`

---

## 3) Voorbeelddiffs

```diff
*** a/vitalign-pro/src/pages/Templates.tsx
--- b/vitalign-pro/src/pages/Templates.tsx
@@
- <Button variant="ghost">Preview</Button>
+{/* Preview verwijderd (Bekijken dekt dit af) */}
  <Button variant="ghost" onClick={() => openView(id)}>Bekijken</Button>
  <Button variant="ghost" onClick={() => openVars(id)}>Variabelen</Button>
  <Button variant="ghost" onClick={() => openTest(id)}>Test</Button>
```

```diff
*** a/backend/api/templates.py
--- b/backend/api/templates.py
@@
 @router.get("/templates/{id}")
 def get_template(id: str):
-    return {"data": TEMPLATES[id], "error": None}
+    t = TEMPLATES[id]
+    return {"data": {
+      "id": id, "name": t["name"], "subject": t["subject"],
+      "body_html": t["body_html"], "body_text": t.get("body_text",""),
+      "required_vars": t.get("required_vars", [])
+    }, "error": None}
@@
 @router.post("/templates/{id}/testsend")
 def testsend(id: str, payload: TestsendPayload):
-    to = payload.to
+    to = payload.to or "punthelderoutreach@gmail.com"
     # render + mailer.send(...)
     return {"data": {"ok": True}, "error": None}
```

---

## 4) QA (manueel)
- “Bekijken” toont HTML + subject; “Text” tab toont text‑variant
- “Variabelen” toont correcte lijst + kopieerbare JSON
- “Test” stuurt mail naar `punthelderoutreach@gmail.com` en toont success‑toast
- Geen nieuwe routes/pages; alles modals
