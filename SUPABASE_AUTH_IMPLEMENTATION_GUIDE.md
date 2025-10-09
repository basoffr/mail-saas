# 🔐 SUPABASE AUTH + RBAC IMPLEMENTATIE GIDS

## ✅ **WAT ER GEDAAN IS**

### **Backend (Python/FastAPI)**
1. ✅ **Auth module** (`backend/app/security/auth.py`)
   - JWT verification via JWKS
   - Bearer token extraction
   - `get_current_user()` dependency
   
2. ✅ **RBAC module** (`backend/app/security/rbac.py`)
   - Role lookup from `profiles` table
   - `require_role()` dependency factory
   - 60s role caching for performance
   
3. ✅ **Auth API** (`backend/app/api/auth.py`)
   - `GET /api/v1/auth/me` - Returns user info + role
   - `POST /api/v1/auth/logout` - Logout logging
   
4. ✅ **Main.py updates**
   - CORS restrictie via `FRONTEND_ORIGIN` env var
   - RBAC guards op alle routes
   - Feature flag: `USE_RBAC=true/false`
   
5. ✅ **Requirements.txt**
   - `python-jose[cryptography]==3.3.0` toegevoegd

### **Database**
6. ✅ **Migration SQL** (`supabase_auth_rbac_migration.sql`)
   - `profiles` table met role check constraint
   - RLS policies
   - Helper function `get_user_role()`

---

## 📋 **IMPLEMENTATIE STAPPEN**

### **STAP 1: Database Setup**

1. **Run migratie in Supabase SQL Editor**:
   ```bash
   # Open: https://supabase.com/dashboard/project/<jouw-project>/sql
   # Copy-paste: supabase_auth_rbac_migration.sql
   # Click: RUN
   ```

2. **Create 3 users in Supabase Auth**:
   ```
   Go to: Authentication → Users → Add user
   
   User 1 (Admin - jij):
   - Email: jouw@email.nl
   - Password: [genereer sterk wachtwoord]
   
   User 2 (Viewer):
   - Email: viewer1@email.nl
   - Password: [genereer sterk wachtwoord]
   
   User 3 (Viewer):
   - Email: viewer2@email.nl
   - Password: [genereer sterk wachtwoord]
   ```

3. **Copy User UUIDs en seed roles**:
   ```sql
   -- In Supabase SQL Editor:
   INSERT INTO profiles (user_id, role) VALUES
     ('<ADMIN_UUID>', 'admin'),
     ('<VIEWER1_UUID>', 'viewer'),
     ('<VIEWER2_UUID>', 'viewer')
   ON CONFLICT (user_id) DO UPDATE SET role = EXCLUDED.role;
   ```

4. **Verify**:
   ```sql
   SELECT 
     p.user_id,
     u.email,
     p.role
```

**Waar vind je deze keys?**
- **SUPABASE_URL**: Project Settings → API → Project URL
- **SUPABASE_ANON_KEY**: Project Settings → API → anon public
- **SUPABASE_SERVICE_ROLE_KEY**: Project Settings → API → service_role (⚠️ geheim!)

---

### **STAP 3: Deploy Backend**

```bash
# Commit alle changes
git add .
git commit -m "🔐 Add Supabase Auth + RBAC"
git push origin main

# Render auto-deploys
# Check logs: https://dashboard.render.com/
```

**Expected logs**:
```
✅ JWKS cached
✅ CORS restricted to: https://mail-saas-xi.vercel.app
🔒 RBAC enabled - applying role-based access control
```

---

### **STAP 4: Test Backend Auth**

**1. Get Access Token (via Supabase)**:
```bash
# Login via Supabase client (of browser console):
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'jouw@email.nl',
  password: 'jouw-wachtwoord'
})

console.log(data.session.access_token)
```

**2. Test /auth/me endpoint**:
```bash
curl -X GET https://mail-saas-rf4s.onrender.com/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# Expected response:
{
  "data": {
    "user_id": "uuid",
    "email": "jouw@email.nl",
    "role": "admin"
  },
  "error": null
}
```

**3. Test RBAC**:
```bash
# Admin kan leads ophalen:
curl -X GET https://mail-saas-rf4s.onrender.com/api/v1/leads \
  -H "Authorization: Bearer <admin_token>"
# → 200 OK

# Viewer kan leads NIET ophalen:
curl -X GET https://mail-saas-rf4s.onrender.com/api/v1/leads \
  -H "Authorization: Bearer <viewer_token>"
# → 403 Forbidden

# Viewer kan stats WEL ophalen:
curl -X GET https://mail-saas-rf4s.onrender.com/api/v1/stats/dashboard \
  -H "Authorization: Bearer <viewer_token>"
# → 200 OK
```

---

### **STAP 5: Frontend Integration**

**1. Install Supabase client** (als nog niet gedaan):
```bash
cd vitalign-pro
npm install @supabase/supabase-js
```

**2. Create Supabase client** (`src/lib/supabase.ts`):
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

**3. Create Auth context** (`src/contexts/AuthContext.tsx`):
```typescript
import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

interface User {
  id: string
  email: string
  role: 'admin' | 'viewer'
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>(undefined!)

export function AuthProvider({ children }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check active sessions
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        fetchUserRole(session.access_token)
      } else {
        setLoading(false)
      }
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (session) {
          await fetchUserRole(session.access_token)
        } else {
          setUser(null)
          setLoading(false)
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  async function fetchUserRole(accessToken: string) {
    try {
      const res = await fetch('https://mail-saas-rf4s.onrender.com/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${accessToken}` }
      })
      const { data } = await res.json()
      setUser({
        id: data.user_id,
        email: data.email,
        role: data.role
      })
    } catch (error) {
      console.error('Failed to fetch user role:', error)
    } finally {
      setLoading(false)
    }
  }

  async function login(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    })
    if (error) throw error
    if (data.session) {
      await fetchUserRole(data.session.access_token)
    }
  }

  async function logout() {
    await supabase.auth.signOut()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
```

**4. Update API client** om token mee te sturen:
```typescript
// src/lib/api.ts
import { supabase } from './supabase'

async function apiCall(endpoint: string, options: RequestInit = {}) {
  const { data: { session } } = await supabase.auth.getSession()
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
  }
  
  const response = await fetch(
    `https://mail-saas-rf4s.onrender.com${endpoint}`,
    { ...options, headers }
  )
  
  return response.json()
}
```

**5. UI Gating** (hide/disable obv role):
```typescript
import { useAuth } from '@/contexts/AuthContext'

function Navigation() {
  const { user } = useAuth()
  
  const canEdit = user?.role === 'admin'
  
  return (
    <nav>
      {/* Always visible */}
      <Link to="/stats">Statistieken</Link>
      <Link to="/inbox">Inbox</Link>
      
      {/* Admin only */}
      {canEdit && (
        <>
          <Link to="/campaigns">Campaigns</Link>
          <Link to="/leads">Leads</Link>
          <Link to="/templates">Templates</Link>
          <Link to="/settings">Settings</Link>
        </>
      )}
    </nav>
  )
}
```

---

## ✅ **ACCEPTATIECRITERIA CHECKLIST**

### **Database**
- [ ] `profiles` table bestaat in Supabase
- [ ] 3 users aangemaakt in Supabase Auth
- [ ] Roles correct gekoppeld via `profiles` tabel
- [ ] Test query: `SELECT * FROM profiles` toont 3 rows

### **Backend Auth**
- [ ] `/api/v1/auth/me` geeft 200 + `{user_id, email, role}`
- [ ] Zonder token → 401 Unauthorized
- [ ] Met invalid token → 401 Unauthorized
- [ ] CORS restricted to `FRONTEND_ORIGIN`

### **Backend RBAC**
- [ ] Viewer: `GET /stats/**` → 200 OK
- [ ] Viewer: `GET /inbox/**` → 200 OK
- [ ] Viewer: `POST /campaigns` → 403 Forbidden
- [ ] Admin: alle routes → 200 OK

### **Frontend**
- [ ] Login flow werkt (email + password)
- [ ] Na login: `/auth/me` wordt gecalled
- [ ] Role wordt opgeslagen in state
- [ ] UI gating: viewer ziet alleen Stats + Inbox
- [ ] UI gating: admin ziet alles
- [ ] Logout werkt (token verwijderd, redirect to login)

---

## 🔧 **TROUBLESHOOTING**

### **401 Unauthorized**
```bash
# Check if token is valid:
curl https://<project>.supabase.co/auth/v1/user \
  -H "Authorization: Bearer <token>"

# Check JWKS endpoint:
curl https://<project>.supabase.co/auth/v1/.well-known/jwks.json
```

### **403 Forbidden**
```bash
# Check role in database:
SELECT * FROM profiles WHERE user_id = '<user_id>';

# Clear role cache (restart backend)
```

### **CORS Error**
```bash
# Check Render env vars:
echo $FRONTEND_ORIGIN
# Must match: https://mail-saas-xi.vercel.app
```

### **Role not found**
```bash
# Verify Supabase service role key is set:
echo $SUPABASE_SERVICE_ROLE_KEY

# Test profiles query directly in Supabase SQL:
SELECT * FROM profiles;
```

---

## 🚀 **NEXT STEPS (Optional)**

### **Later improvements**:
1. **TOTP 2FA** voor admin account
2. **Audit log** voor login/logout events
3. **Password reset flow** via Supabase
4. **Session timeout** warnings
5. **Role management UI** (admin kan rollen wijzigen)

---

## 📚 **REFERENCES**

- **Supabase Auth Docs**: https://supabase.com/docs/guides/auth
- **JWT Verification**: https://supabase.com/docs/guides/auth/server-side/verifying-jwt
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **RBAC Pattern**: https://www.osohq.com/academy/what-is-role-based-access-control-rbac

---

**KLAAR OM TE STARTEN? Begin met STAP 1! 🚀**
