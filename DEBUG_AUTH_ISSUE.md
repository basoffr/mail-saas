# 🐛 AUTH 401 DEBUG GUIDE

## PROBLEEM
- Login werkt ✅
- `/auth/me` geeft 401 ❌
- User wordt automatisch uitgelogd

## MOGELIJKE OORZAKEN

### 1. JWKS URL verkeerd geconfigureerd
**Check in Render**:
```
SUPABASE_JWKS_URL=https://zpnklihryhpkaiyubkfn.supabase.co/auth/v1/.well-known/jwks.json
```

**Verify**: URL moet eindigen met `/auth/v1/.well-known/jwks.json`

### 2. JWKS ophalen faalt
**Render logs zouden moeten tonen**:
```
❌ Error: Failed to fetch JWKS from ...
OF
✅ JWKS cached (expires in 3600s)
```

### 3. JWT verification faalt
**Mogelijke redenen**:
- JWT is verlopen
- JWT audience/issuer komt niet overeen
- JWKS public key mismatch

---

## 🔧 QUICK FIX OPTIES

### OPTIE A: Tijdelijk RBAC uitzetten ⚡
**In Render Environment Variables**:
```
USE_RBAC=false
```
→ App werkt weer zoals voorheen
→ Geeft tijd om JWT issue te debuggen

### OPTIE B: Check Render Logs 🔍

**Ga naar**: https://dashboard.render.com/web/[your-service]/logs

**Zoek naar**:
```
🔄 Using new auth system
✅ JWKS cached
❌ JWT verification failed
❌ Invalid JWT
❌ Failed to fetch JWKS
```

### OPTIE C: Test JWKS URL Handmatig 🧪

**Test in browser**:
```
https://zpnklihryhpkaiyubkfn.supabase.co/auth/v1/.well-known/jwks.json
```

**Verwacht**:
```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "...",
      "n": "...",
      "e": "AQAB",
      ...
    }
  ]
}
```

---

## 🐛 DEBUG STEPS

### STEP 1: Check Render Environment Variables
```bash
✅ USE_RBAC=true
✅ SUPABASE_URL=https://zpnklihryhpkaiyubkfn.supabase.co
✅ SUPABASE_JWKS_URL=https://zpnklihryhpkaiyubkfn.supabase.co/auth/v1/.well-known/jwks.json
✅ SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
✅ CORS_ORIGINS=https://mail-saas-xi.vercel.app,https://mail-saas.vercel.app
```

### STEP 2: Check Render Logs
**Look for startup messages**:
```
✅ CORS restricted to: ['https://mail-saas-xi.vercel.app', ...]
✅ RBAC enabled - applying role-based access control
🔄 core/auth.py redirecting to security/auth.py (RBAC enabled)
```

**Look for JWT errors**:
```
❌ JWT verification failed: ...
❌ Invalid JWT signature
❌ JWT expired
❌ Failed to fetch JWKS
```

### STEP 3: Get JWT Token from Browser
**Open browser console**:
```javascript
// Get current session
const { data: { session } } = await supabase.auth.getSession()
console.log('Token:', session.access_token)

// Copy token en test op jwt.io
```

**Paste in**: https://jwt.io

**Verify**:
- Header: `"alg": "HS256"` (Supabase uses HS256)
- Payload: `"iss": "https://zpnklihryhpkaiyubkfn.supabase.co/auth/v1"`
- Not expired: `exp` timestamp > now

### STEP 4: Test Backend Directly
**Using curl**:
```bash
# Get token from browser console first
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl https://mail-saas-rf4s.onrender.com/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" \
  -v
```

**Expected success**:
```json
{
  "data": {
    "user_id": "...",
    "email": "info@boffringadigital.nl",
    "role": "admin"
  },
  "error": null
}
```

**Expected error**:
```json
{
  "detail": "Could not validate credentials"
}
```

---

## 🔥 MOST LIKELY ISSUES

### Issue 1: JWKS URL Missing `/auth/v1/`
**Wrong**:
```
SUPABASE_JWKS_URL=https://zpnklihryhpkaiyubkfn.supabase.co/.well-known/jwks.json
```

**Correct**:
```
SUPABASE_JWKS_URL=https://zpnklihryhpkaiyubkfn.supabase.co/auth/v1/.well-known/jwks.json
```

### Issue 2: JWT Algorithm Mismatch
**Supabase uses HS256** but backend expects RS256 (JWKS).

**Fix**: Backend code should handle HS256 for Supabase:
- Supabase Auth JWTs are signed with HS256
- JWKS is for RS256 (public/private key pairs)
- We need to use the JWT_SECRET instead!

**THIS IS THE REAL PROBLEM!**

---

## 🎯 ACTUAL ROOT CAUSE

**Supabase Auth JWTs use HS256** (symmetric key), NOT RS256 (asymmetric/JWKS).

Our backend code expects JWKS (RS256) but Supabase uses HS256 with a secret key.

### SOLUTION: Update Backend JWT Verification

We need to:
1. Use `SUPABASE_JWT_SECRET` instead of JWKS
2. Verify with HS256 algorithm
3. Get JWT secret from Supabase dashboard

**Where to find JWT Secret**:
- https://supabase.com/dashboard/project/zpnklihryhpkaiyubkfn/settings/api
- Under "JWT Settings" → "JWT Secret" (click Reveal)

---

## 🚀 IMMEDIATE ACTION REQUIRED

**Option 1**: Update backend to use JWT_SECRET (proper fix)
**Option 2**: Set `USE_RBAC=false` temporarily (quick workaround)

Let me know which option you prefer!
