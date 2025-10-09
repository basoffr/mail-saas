# 🔑 SUPABASE JWT SECRET SETUP

## 🎯 **WAT IS ER VERANDERD?**

**Oude implementatie (fout)**:
- ❌ Gebruikte JWKS/RS256 (asymmetric keys)
- ❌ `SUPABASE_JWKS_URL` environment variable
- ❌ Complexe JWKS caching logica

**Nieuwe implementatie (correct)**:
- ✅ Gebruikt HS256 (symmetric key)
- ✅ `SUPABASE_JWT_SECRET` environment variable
- ✅ Simpele, directe JWT verificatie

---

## 📋 **STAP 1: JWT SECRET OPHALEN**

### **Ga naar Supabase Dashboard**:
```
https://supabase.com/dashboard/project/zpnklihryhpkaiyubkfn/settings/api
```

### **Scroll naar "JWT Settings"**:
1. Zoek sectie "JWT Settings"
2. Klik **"Reveal"** naast "JWT Secret"
3. Copy de hele string (lang, begint met letters/cijfers)

**Voorbeeld** (dit is NIET jouw echte secret):
```
your-jwt-secret-here-very-long-string-of-random-characters
```

---

## ⚙️ **STAP 2: RENDER ENV VARS UPDATEN**

### **Ga naar Render Dashboard**:
```
https://dashboard.render.com/web/[your-service]/env
```

### **Update/Add deze variables**:

**NIEUW (toevoegen)**:
```
SUPABASE_JWT_SECRET=<paste-jwt-secret-here>
```

**VERWIJDER (oude, niet meer nodig)**:
```
SUPABASE_JWKS_URL  ← DELETE THIS
```

**BEHOUDEN (deze blijven staan)**:
```
USE_RBAC=true
SUPABASE_URL=https://zpnklihryhpkaiyubkfn.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
CORS_ORIGINS=https://mail-saas-xi.vercel.app,https://mail-saas.vercel.app
```

### **Save & Redeploy**

Render zal automatisch rebuilden met nieuwe env vars (2-3 min).

---

## 🧪 **STAP 3: TEST DE FIX**

### **Test 1: Login**
1. Ga naar: https://mail-saas-xi.vercel.app
2. Login met: `info@boffringadigital.nl`
3. **Verwacht**: Successvolle login, redirect naar /leads

### **Test 2: Check Console**
**Browser console moet tonen**:
```
Auth state changed: SIGNED_IN info@boffringadigital.nl
✅ User role fetched: admin
```

**GEEN errors meer**:
```
❌ GET .../auth/me 401 (Unauthorized)  ← DEZE MAG ER NIET MEER ZIJN
❌ Error fetching user role            ← DEZE MAG ER NIET MEER ZIJN
❌ Auth state changed: SIGNED_OUT       ← DEZE MAG ER NIET MEER ZIJN
```

### **Test 3: Check Render Logs**
```
✅ JWT secret configured for HS256 verification
✅ JWT verified for user: info@boffringadigital.nl
✅ CORS restricted to: ['https://mail-saas-xi.vercel.app', ...]
🔒 RBAC enabled - applying role-based access control
```

---

## 📊 **VOLLEDIGE ENV VAR LIJST**

**Render Backend Environment Variables**:
```bash
# Database
SUPABASE_URL=https://zpnklihryhpkaiyubkfn.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

# Auth (NIEUW!)
SUPABASE_JWT_SECRET=<your-jwt-secret>
USE_RBAC=true

# CORS
CORS_ORIGINS=https://mail-saas-xi.vercel.app,https://mail-saas.vercel.app

# ... (alle andere env vars blijven hetzelfde)
```

**Vercel Frontend Environment Variables** (onveranderd):
```bash
VITE_SUPABASE_URL=https://zpnklihryhpkaiyubkfn.supabase.co
VITE_SUPABASE_ANON_KEY=<your-anon-key>
VITE_API_BASE_URL=https://mail-saas-rf4s.onrender.com/api/v1
VITE_API_TIMEOUT=30000
```

---

## ✅ **SUCCESS CHECKLIST**

- [ ] JWT Secret opgehaald van Supabase Dashboard
- [ ] `SUPABASE_JWT_SECRET` toegevoegd in Render
- [ ] `SUPABASE_JWKS_URL` verwijderd uit Render (oude var)
- [ ] Render redeploy succesvol (check logs)
- [ ] Login werkt zonder errors
- [ ] Console toont "User role fetched: admin"
- [ ] Geen 401 errors meer in console
- [ ] Render logs tonen "JWT verified for user"

---

## 🐛 **TROUBLESHOOTING**

### **Probleem: Nog steeds 401 errors**
**Mogelijke oorzaken**:
1. JWT Secret niet correct gekopieerd
2. Render heeft nog niet gerebuild
3. Browser cache (hard refresh: Ctrl+Shift+R)

**Oplossing**:
- Check Render logs voor "JWT secret configured"
- Verify env var in Render dashboard (geen spaties, exact gekopieerd)
- Clear browser cache + hard refresh

### **Probleem: "SUPABASE_JWT_SECRET must be set"**
**Oorzaak**: Env var niet gezet in Render

**Oplossing**:
- Ga naar Render → Environment
- Add `SUPABASE_JWT_SECRET` variable
- Save (triggers rebuild)

### **Probleem: "Invalid token" errors**
**Mogelijke oorzaken**:
1. Verkeerde JWT secret
2. Token expired
3. Browser cached old token

**Oplossing**:
- Logout + login again (nieuwe token)
- Check JWT secret is exact dezelfde als in Supabase
- Test token op jwt.io (should be HS256, not RS256)

---

## 🎉 **KLAAR!**

Na deze stappen:
- ✅ Backend verifieert JWTs correct met HS256
- ✅ Login werkt zonder 401 errors
- ✅ RBAC werkt (admin vs viewer)
- ✅ Frontend + Backend communiceren succesvol

**Totale tijd: 5-10 minuten** 🚀
