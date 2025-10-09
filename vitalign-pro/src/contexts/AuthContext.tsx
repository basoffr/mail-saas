import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { Session, User as SupabaseUser } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { useToast } from '@/hooks/use-toast'

export type UserRole = 'admin' | 'viewer'

export interface User {
  id: string
  email: string
  role: UserRole
}

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  canEdit: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    // Check active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      if (session) {
        fetchUserRole(session.access_token)
      } else {
        setLoading(false)
      }
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('Auth state changed:', event, session?.user?.email)
      setSession(session)
      
      if (session) {
        await fetchUserRole(session.access_token)
      } else {
        setUser(null)
        setLoading(false)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  async function fetchUserRole(accessToken: string) {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch user role')
      }

      const { data } = await response.json()
      
      setUser({
        id: data.user_id,
        email: data.email,
        role: data.role as UserRole,
      })
      
      console.log('User role fetched:', data.role)
    } catch (error) {
      console.error('Error fetching user role:', error)
      toast({
        title: 'Error',
        description: 'Failed to load user profile. Please try logging in again.',
        variant: 'destructive',
      })
      await supabase.auth.signOut()
    } finally {
      setLoading(false)
    }
  }

  async function login(email: string, password: string) {
    try {
      setLoading(true)
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) throw error

      if (data.session) {
        await fetchUserRole(data.session.access_token)
        toast({
          title: 'Success',
          description: 'Successfully logged in!',
        })
      }
    } catch (error: any) {
      console.error('Login error:', error)
      toast({
        title: 'Login Failed',
        description: error.message || 'Invalid email or password',
        variant: 'destructive',
      })
      throw error
    } finally {
      setLoading(false)
    }
  }

  async function logout() {
    try {
      setLoading(true)
      await supabase.auth.signOut()
      setUser(null)
      setSession(null)
      toast({
        title: 'Success',
        description: 'Successfully logged out',
      })
    } catch (error: any) {
      console.error('Logout error:', error)
      toast({
        title: 'Error',
        description: 'Failed to log out',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const canEdit = user?.role === 'admin'

  return (
    <AuthContext.Provider value={{ user, session, loading, login, logout, canEdit }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
