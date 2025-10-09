# 🔐 AUTH MODULES UITLEG

## 📂 **3 AUTH.PY BESTANDEN - GEEN CONFLICT**

### **1. `app/api/auth.py`** ✅
**Doel**: API endpoints voor authentication  
**Endpoints**:
- `GET /api/v1/auth/me` - Haal user info + role op
- `POST /api/v1/auth/logout` - Logout logging

**Usage**: Frontend calls deze endpoints  
**Status**: **Nieuw** (Supabase Auth implementatie)

---

### **2. `app/security/auth.py`** ✅
**Doel**: JWT verification via Supabase JWKS  
**Exports**:
- `get_current_user()` - FastAPI dependency voor JWT verificatie
- `JWKSCache` - Cache voor JWKS keys
- `verify_supabase_jwt()` - JWT verification functie

**Usage**: Backend dependencies  
**Status**: **Nieuw** (Supabase Auth implementatie)

---

### **3. `app/core/auth.py`** ⚠️ **DEPRECATED**
**Doel**: **Compatibility shim** voor backward compatibility  
**Exports**:
- `require_auth` - Oude dependency naam

**Behavior**:
```python
if USE_RBAC=true:
    require_auth = get_current_user  # Redirect naar security/auth.py
else:
    require_auth = legacy_stub  # Accepteert any Bearer token
```

**Usage**: Oude API routes die nog `from app.core.auth import require_auth` gebruiken  
**Status**: **Deprecated** maar werkt nog (compatibility)

---

## 🔄 **HOE ZE SAMENWERKEN**

### **Scenario 1: USE_RBAC=false (Development)**
```
┌─────────────┐
│ API Routes  │ 
│  Depends(   │
│ require_auth│──┐
│  )          │  │
└─────────────┘  │
                 ▼
         ┌───────────────┐
         │ core/auth.py  │
         │ Legacy stub   │
         │ (any token OK)│
         └───────────────┘
```

### **Scenario 2: USE_RBAC=true (Production)**
```
┌─────────────┐
│ API Routes  │ 
│  Depends(   │
│ require_auth│──┐
│  )          │  │
└─────────────┘  │
                 ▼
         ┌───────────────┐
         │ core/auth.py  │──────▶ security/auth.py
         │ Compatibility │        (JWT verify)
         │ shim          │             │
         └───────────────┘             │
                                       ▼
         ┌──────────────────────────────┐
         │ main.py                      │
         │ RBAC via require_role()      │
         │ (admin/viewer check)         │
         └──────────────────────────────┘
```

---

## ✅ **WAAROM DIT WERKT**

1. **Backward Compatibility**: Oude routes hoeven niet gewijzigd te worden
2. **Gradual Migration**: `USE_RBAC` flag schakelt tussen oud/nieuw
3. **Tests Blijven Werken**: Tests mocken `core/auth.require_auth`
4. **Production Ready**: Set `USE_RBAC=true` voor Supabase JWT

---

## 🚀 **DEPLOYMENT CHECKLIST**

### **Development (USE_RBAC=false)**
```bash
USE_RBAC=false
# → Oude stub, accepteert any Bearer token
# → Tests werken
# → Geen Supabase JWT verification
```

### **Production (USE_RBAC=true)**
```bash
USE_RBAC=true
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_JWKS_URL=${SUPABASE_URL}/auth/v1/.well-known/jwks.json
SUPABASE_SERVICE_ROLE_KEY=<key>
FRONTEND_ORIGIN=https://mail-saas-xi.vercel.app

# → core/auth.py redirect naar security/auth.py
# → JWT verification via JWKS
# → Role checks via profiles table
# → CORS restricted
```

---

## 📊 **MIGRATION PLAN (Later)**

**Phase 1** (Nu): ✅ Compatibility shim in place  
**Phase 2** (Later): Update alle routes naar `from app.security.auth import get_current_user`  
**Phase 3** (Later): Verwijder `app/core/auth.py` volledig

---

## 🧪 **TESTEN**

### **Test zonder RBAC**:
```bash
curl https://mail-saas-rf4s.onrender.com/api/v1/leads \
  -H "Authorization: Bearer any-token-works"
# → 200 OK (legacy stub accepteert any token)
```

### **Test met RBAC**:
```bash
# Set USE_RBAC=true in Render

curl https://mail-saas-rf4s.onrender.com/api/v1/leads \
  -H "Authorization: Bearer invalid-token"
# → 401 Unauthorized (JWT verification fails)

curl https://mail-saas-rf4s.onrender.com/api/v1/leads \
  -H "Authorization: Bearer <valid-supabase-token>"
# → 200 OK (if admin) or 403 Forbidden (if viewer)
```

---

## 💡 **CONCLUSIE**

**Geen conflict!** De 3 auth.py bestanden werken samen:
- `api/auth.py` = Endpoints
- `security/auth.py` = JWT verification
- `core/auth.py` = Compatibility shim (redirects naar security/auth.py als USE_RBAC=true)

**Action**: Zet `USE_RBAC=true` in Render voor production auth! 🚀
