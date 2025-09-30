# ✅ Handtekening Implementatie - Complete

**Datum:** 30 September 2025, 20:26 CET  
**Status:** 🟢 **FULLY IMPLEMENTED**

---

## 🎯 Objective

Handtekeningen van Christian en Victor automatisch toevoegen aan templates:
- **Mail 1-2** (christian alias) → Christian Handtekening.png
- **Mail 3-4** (victor alias) → Victor Handtekening.png
- **Locatie:** Helemaal onderaan de email (voor tracking pixel)

---

## ✅ Implementation

### 1. Signature Images Opgeslagen

**Locatie:**
```
backend/app/assets/signatures/
├── Christian Handtekening.png
└── Victor Handtekening.png
```

**Source:** Gekopieerd van root directory naar assets folder.

---

### 2. Signature Injector Service

**File:** `backend/app/services/signature_injector.py`

**Functies:**

#### `inject_signature_cid(html, alias)` 
Voegt handtekening toe als CID (Content-ID) reference in HTML:

```python
# Voor christian (mail 1-2):
<img src="cid:signature_christian" alt="Christian Handtekening" 
     style="max-width: 300px; height: auto;" />

# Voor victor (mail 3-4):
<img src="cid:signature_victor" alt="Victor Handtekening" 
     style="max-width: 300px; height: auto;" />
```

**Styling:**
- `margin-top: 30px` - ruimte boven handtekening
- `margin-bottom: 20px` - ruimte onder handtekening
- `max-width: 300px` - responsive sizing
- `display: block` - eigen regel

**Injectie locatie:** Voor `</body>` tag (na content, vóór tracking pixel)

#### `get_alias_from_mail_number(mail_number)`
Bepaalt alias op basis van mail nummer:
```python
mail_number 1-2 → "christian"
mail_number 3-4 → "victor"
```

#### `get_signature_path_for_alias(alias)`
Geeft bestandspad naar juiste handtekening:
```python
"christian" → "signatures/Christian Handtekening.png"
"victor" → "signatures/Victor Handtekening.png"
```

---

### 3. Message Sender Integration

**File:** `backend/app/services/message_sender.py`

**Changes:**

#### Import toegevoegd:
```python
from app.services.signature_injector import (
    inject_signature_cid, 
    get_alias_from_mail_number
)
```

#### HTML Injection (line ~148):
```python
# Bepaal alias op basis van mail_number
alias = get_alias_from_mail_number(message.mail_number)

# Inject handtekening in HTML
template_content = inject_signature_cid(template_content, alias)

logger.debug(f"Injected {alias} signature for message {message.id}")
```

#### CID Attachment (line ~203-221):
```python
# Attach signature image as embedded CID
from email.mime.image import MIMEImage
from pathlib import Path

alias = get_alias_from_mail_number(message.mail_number)
signature_filename = f"{alias.capitalize()} Handtekening.png"
signature_path = Path(__file__).parent.parent / "assets" / "signatures" / signature_filename

if signature_path.exists():
    with open(signature_path, 'rb') as img_file:
        img_data = img_file.read()
        image = MIMEImage(img_data)
        image.add_header('Content-ID', f'<signature_{alias}>')
        image.add_header('Content-Disposition', 'inline', filename=signature_filename)
        msg.attach(image)
        logger.debug(f"Attached {alias} signature image as CID")
else:
    logger.warning(f"Signature image not found: {signature_path}")
```

#### MIME Type Changed:
```python
# Was: MIMEMultipart('alternative')
# Nu:  MIMEMultipart('related')  # Voor embedded images
```

---

## 📧 Email Structure

### Final Email Structuur:
```
MIMEMultipart('related')
├── Headers
│   ├── From: christian@{domain}
│   ├── To: {lead.email}
│   ├── Subject: {template.subject}
│   ├── Reply-To: {reply_to}
│   └── List-Unsubscribe: {unsub_headers}
│
├── HTML Body (MIMEText)
│   ├── Email content
│   ├── <img src="cid:signature_{alias}" />  ← Handtekening
│   └── <img src="{tracking_pixel}" />       ← Tracking pixel
│
└── Embedded Images (MIMEImage)
    └── Content-ID: signature_{alias}  ← PNG data
```

---

## 🔄 Injection Order

**Volgorde van transformaties:**

1. **Template rendering** - variabelen vervangen
2. **Signature injection** ← NEW! Handtekening HTML
3. **Tracking pixel** - open tracking
4. **CID attachment** ← NEW! Handtekening PNG

**Waarom deze volgorde?**
- Handtekening VOOR tracking pixel → handtekening zichtbaar onderaan
- CID attachment NA HTML → MIME structuur correct
- Tracking pixel LAATST → onderaan HTML (onzichtbaar)

---

## 🎯 Per Mail Type

### Mail 1 (dag 0) - Christian
```
FROM: christian@punthelder-vindbaarheid.nl
BODY: 
  [content]
  <img src="cid:signature_christian" />  ← Christian Handtekening.png
  <img src="...tracking..." />
ATTACHMENTS:
  - signature_christian (Christian Handtekening.png)
```

### Mail 2 (dag +3) - Christian
```
FROM: christian@punthelder-vindbaarheid.nl
BODY:
  [content]
  <img src="cid:signature_christian" />  ← Christian Handtekening.png
  <img src="...tracking..." />
ATTACHMENTS:
  - signature_christian (Christian Handtekening.png)
```

### Mail 3 (dag +6) - Victor
```
FROM: victor@punthelder-vindbaarheid.nl
REPLY-TO: christian@punthelder-vindbaarheid.nl
BODY:
  [content]
  <img src="cid:signature_victor" />  ← Victor Handtekening.png
  <img src="...tracking..." />
ATTACHMENTS:
  - signature_victor (Victor Handtekening.png)
```

### Mail 4 (dag +9) - Victor
```
FROM: victor@punthelder-vindbaarheid.nl
REPLY-TO: christian@punthelder-vindbaarheid.nl
BODY:
  [content]
  <img src="cid:signature_victor" />  ← Victor Handtekening.png
  <img src="...tracking..." />
ATTACHMENTS:
  - signature_victor (Victor Handtekening.png)
```

---

## 🧪 Testing Checklist

### Backend Tests
- [ ] Test `get_alias_from_mail_number(1)` → "christian"
- [ ] Test `get_alias_from_mail_number(3)` → "victor"
- [ ] Test `inject_signature_cid()` voegt `<img src="cid:signature_{alias}"` toe
- [ ] Test signature path resolution
- [ ] Test CID attachment wordt toegevoegd aan MIME message

### Integration Tests
- [ ] Send mail 1 → Christian handtekening visible
- [ ] Send mail 2 → Christian handtekening visible
- [ ] Send mail 3 → Victor handtekening visible
- [ ] Send mail 4 → Victor handtekening visible
- [ ] Verify handtekening appears BEFORE tracking pixel
- [ ] Verify handtekening is embedded (not external URL)

### Visual Tests
- [ ] Open email in Gmail → handtekening zichtbaar
- [ ] Open email in Outlook → handtekening zichtbaar
- [ ] Check mobile view → handtekening responsive
- [ ] Verify size: max 300px width

---

## 📁 Files Changed

### New Files
1. ✅ `backend/app/services/signature_injector.py` - Signature injection service
2. ✅ `backend/app/assets/signatures/Christian Handtekening.png` - Image
3. ✅ `backend/app/assets/signatures/Victor Handtekening.png` - Image

### Modified Files
1. ✅ `backend/app/services/message_sender.py` - Integration

---

## 🚀 Deployment Notes

### Files to Deploy
- `backend/app/services/signature_injector.py` (NEW)
- `backend/app/services/message_sender.py` (MODIFIED)
- `backend/app/assets/signatures/*.png` (2 files)

### No Breaking Changes
- ✅ Backward compatible
- ✅ No database changes
- ✅ No API changes
- ✅ Existing templates keep working

### Environment Variables
No new environment variables required.

---

## ✅ Success Criteria

All criteria MET:

- [x] Handtekening images opgeslagen in assets folder
- [x] Signature injector service created
- [x] Mail 1-2 krijgen Christian handtekening
- [x] Mail 3-4 krijgen Victor handtekening  
- [x] Handtekening staat onderaan email
- [x] Handtekening is embedded (CID), niet external URL
- [x] Handtekening staat VOOR tracking pixel
- [x] Responsive styling (max 300px)

---

## 📈 Next Steps (Optional)

### Short Term
- [ ] Test verzenden van emails met handtekeningen
- [ ] Verify in verschillende email clients
- [ ] Check spam score met handtekeningen

### Medium Term
- [ ] Optimize image sizes (PNG → WebP?)
- [ ] Add retina @2x versions
- [ ] Cache signature images in memory

### Long Term
- [ ] Dynamic signatures per campaign
- [ ] Signature A/B testing
- [ ] Analytics: track signature visibility

---

**Implementation Time:** ~30 minuten  
**Status:** ✅ **COMPLETE & READY FOR TESTING**  
**Testing Required:** Email sending + visual verification
