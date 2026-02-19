'use client'

/**
 * AuthContext — MindMate.
 * 
 * React Context that provides auth state across the entire app.
 * Wraps the app in layout.jsx so every component can access
 * user, session, signIn, signUp, signOut.
 * 
 * WHY context instead of prop drilling:
 * - Auth state is needed in page.jsx, PreferencesModal, FeedbackPanel
 * - Context prevents passing user through 5+ component levels
 * - Auth state listener auto-updates on token refresh
 */

import { createContext, useContext, useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'

const AuthContext = createContext({})

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true) // true until initial check completes

  useEffect(() => {
    // 1. Check existing session on mount
    supabase.auth.getSession().then(({ data: { session: s } }) => {
      setSession(s)
      setUser(s?.user || null)
      setLoading(false)
    })

    // 2. Listen for auth state changes (login, logout, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, s) => {
        setSession(s)
        setUser(s?.user || null)
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  /**
   * Sign in with email + password.
   * @returns {{ error: Error | null }}
   */
  const signIn = async (email, password) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    return { error }
  }

  /**
   * Sign up with email + password.
   * @returns {{ error: Error | null }}
   */
  const signUp = async (email, password) => {
    const { error } = await supabase.auth.signUp({ email, password })
    return { error }
  }

  /**
   * Sign out and clear session.
   */
  const signOut = async () => {
    await supabase.auth.signOut()
    setUser(null)
    setSession(null)
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook to access auth state from any component.
 * Usage: const { user, signOut } = useAuth()
 */
export function useAuth() {
  return useContext(AuthContext)
}
