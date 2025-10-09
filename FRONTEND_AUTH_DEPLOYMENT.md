# 🚀 FRONTEND AUTH DEPLOYMENT GUIDE

## ✅ **WHAT WAS IMPLEMENTED**

### **Frontend Components Created**
1. ✅ **Supabase Client** (`src/lib/supabase.ts`)
2. ✅ **Auth Context** (`src/contexts/AuthContext.tsx`)
3. ✅ **Login Page** (`src/pages/Login.tsx`)
4. ✅ **Protected Route** (`src/components/auth/ProtectedRoute.tsx`)
5. ✅ **API Client Update** (`src/services/auth.ts`)
6. ✅ **App Routing** (`src/App.tsx`)
7. ✅ **Sidebar UI Gating** (`src/components/layout/AppSidebar.tsx`)

### **Features**
- ✅ JWT token management via Supabase Auth
- ✅ Protected routes (redirect to login if not authenticated)
- ✅ Role-based UI gating (admin vs viewer)
- ✅ Auto-refresh tokens
- ✅ Persistent sessions
- ✅ Logout functionality

---

## 📦 **STEP 1: INSTALL DEPENDENCIES**

```bash
cd vitalign-pro
npm install @supabase/supabase-js
```

**Verify installation**:
```bash
npm list @supabase/supabase-js
# Should show: @supabase/supabase-js@2.x.x
```

---

## ⚙️ **STEP 2: ENVIRONMENT VARIABLES**

### **Create `.env` file** (if not exists):
```bash
# In vitalign-pro directory
touch .env
```

### **Add these variables**:
```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://zpnklihryhpkaiyubkfn.supabase.co
VITE_SUPABASE_ANON_KEY=<your-anon-key-here>

# API Configuration
VITE_API_BASE_URL=https://mail-saas-rf4s.onrender.com/api/v1
VITE_API_TIMEOUT=30000
```

**Where to find these values**:
- Go to: https://supabase.com/dashboard/project/zpnklihryhpkaiyubkfn/settings/api
- **VITE_SUPABASE_URL**: Project URL (at the top)
- **VITE_SUPABASE_ANON_KEY**: Under "Project API keys" → anon public (click "Reveal")

---

## 🎨 **STEP 3: VERCEL ENVIRONMENT VARIABLES**

### **Go to Vercel Dashboard**:
```
https://vercel.com/your-team/mail-saas/settings/environment-variables
```

### **Add these variables**:
```
VITE_SUPABASE_URL = https://zpnklihryhpkaiyubkfn.supabase.co
VITE_SUPABASE_ANON_KEY = <your-anon-key>
VITE_API_BASE_URL = https://mail-saas-rf4s.onrender.com/api/v1
VITE_API_TIMEOUT = 30000
```

**Environment**: Production + Preview + Development

---

## 🔧 **STEP 4: BACKEND ENV VARS (Already Done)**

Verify these are set in Render:
```bash
USE_RBAC=true
SUPABASE_URL=https://zpnklihryhpkaiyubkfn.supabase.co
SUPABASE_JWKS_URL=https://zpnklihryhpkaiyubkfn.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
CORS_ORIGINS=https://mail-saas-xi.vercel.app,https://mail-saas.vercel.app
```

---

## 🚀 **STEP 5: BUILD & DEPLOY**

### **Local Test** (optional):
```bash
cd vitalign-pro
npm run dev
# Visit: http://localhost:5173
# Should redirect to /login
```

### **Deploy to Vercel**:
```bash
git add .
git commit -m "Add Supabase Auth + RBAC frontend"
git push origin main
```

**Vercel auto-deploys** from main branch.

---

## 🧪 **STEP 6: TEST THE FLOW**

### **Test 1: Login as Admin**
1. Visit: https://mail-saas-xi.vercel.app
2. Should redirect to `/login`
3. Login:
   - Email: `info@boffringadigital.nl`
   - Password: [your password]
4. Should redirect to `/leads`
5. **Check sidebar**: Should see ALL menu items

### **Test 2: Login as Viewer**
1. Logout (if logged in)
2. Login:
   - Email: `christian@punthelder.nl`
   - Password: [your password]
3. Should redirect to `/stats` (first accessible page)
4. **Check sidebar**: Should only see:
   - ✅ Statistieken
   - ✅ Inbox
   - ❌ Other menu items hidden

### **Test 3: Protected Routes**
**As Viewer**, try to manually visit:
```
https://mail-saas-xi.vercel.app/leads
```
→ Should show "Geen toegang" message

### **Test 4: API Calls**
**Open browser console**, check for:
```javascript
API Call: { method: 'GET', url: '...', hasAuth: true }
✅ User role fetched: admin
```

---

## 🐛 **TROUBLESHOOTING**

### **Issue 1: Redirect loop**
**Symptom**: Page keeps redirecting to /login
**Solution**: 
- Check browser console for errors
- Verify Supabase env vars are correct
- Clear localStorage: `localStorage.clear()`

### **Issue 2: 401 Unauthorized**
**Symptom**: API calls fail with 401
**Solution**:
- Check Render logs: `USE_RBAC=true`
- Verify `SUPABASE_JWKS_URL` is correct
- Test token: Copy from Network tab → jwt.io

### **Issue 3: Cannot find module '@supabase/supabase-js'**
**Symptom**: TypeScript errors
**Solution**:
```bash
cd vitalign-pro
npm install @supabase/supabase-js
```

### **Issue 4: CORS errors**
**Symptom**: `Access-Control-Allow-Origin` error
**Solution**:
- Check Render env: `CORS_ORIGINS` includes Vercel domain
- Check Render logs for CORS message

---

## 📊 **EXPECTED BEHAVIOR**

### **Admin User** (`info@boffringadigital.nl`):
```
✅ Can access: ALL pages
✅ Sidebar shows: ALL menu items
✅ Can: Create campaigns, edit leads, upload reports, etc.
```

### **Viewer User** (`christian@punthelder.nl`, `victor@punthelder.nl`):
```
✅ Can access: Statistics, Inbox (read-only)
❌ Cannot access: Leads, Campaigns, Templates, Reports, Settings
✅ Sidebar shows: Only Stats + Inbox
❌ Manual URL access: Blocked with "Geen toegang"
```

---

## ✅ **SUCCESS CHECKLIST**

- [ ] `@supabase/supabase-js` installed
- [ ] `.env` file has correct Supabase credentials
- [ ] Vercel env vars set
- [ ] Render env vars verified (USE_RBAC=true)
- [ ] Git pushed to main
- [ ] Vercel deployed successfully
- [ ] Can login as admin
- [ ] Can login as viewer
- [ ] Viewer sees limited menu
- [ ] Viewer cannot access protected routes
- [ ] API calls include Bearer token
- [ ] No console errors

---

## 🎯 **NEXT STEPS** (Optional)

1. **Add logout button** to AppTopbar
2. **Add user profile dropdown** with email + role display
3. **Add password reset flow**
4. **Add session timeout warnings**
5. **Add audit logging** for login/logout events

---

**🎉 PRODUCTION AUTH IS READY!**
