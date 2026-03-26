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

  const resolveValidSession = async () => {
    const { data: { session: current } } = await supabase.auth.getSession()
    if (!current) return null

    const expiresSoon = current.expires_at
      ? (current.expires_at * 1000) <= (Date.now() + 60_000)
      : false

    if (expiresSoon) {
      const { data, error } = await supabase.auth.refreshSession()
      if (!error && data?.session) {
        return data.session
      }
    }

    // Validate token against Supabase auth; if invalid, try one refresh.
    const { error: validateError } = await supabase.auth.getUser(current.access_token)
    if (!validateError) return current

    const { data, error } = await supabase.auth.refreshSession()
    if (error) return null
    return data?.session || null
  }

  useEffect(() => {
    let active = true

    const syncSession = async () => {
      const valid = await resolveValidSession()
      if (!active) return
      setSession(valid)
      setUser(valid?.user || null)
      setLoading(false)
    }

    // 1. Check existing session on mount
    syncSession()

    // 2. Listen for auth state changes (login, logout, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, s) => {
        if (!active) return

        if (s) {
          const valid = await resolveValidSession()
          if (!active) return
          setSession(valid)
          setUser(valid?.user || null)
          setLoading(false)
          return
        }

        if (event === 'SIGNED_OUT') {
          setSession(null)
          setUser(null)
          setLoading(false)
          return
        }

        // Avoid false-negative auth flips on transient events.
        const latest = await resolveValidSession()
        if (!active) return
        setSession(latest || null)
        setUser(latest?.user || null)
        setLoading(false)
      }
    )

    return () => {
      active = false
      subscription.unsubscribe()
    }
  }, [])

  /**
   * Sign in with email + password.
   * @returns {{ error: Error | null }}
   */
  const signIn = async (email, password) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      return { error, session: null }
    }

    const currentSession = await resolveValidSession()
    if (!currentSession) {
      return {
        error: new Error('No active session. If you just signed up, verify your email first.'),
        session: null,
      }
    }

    setSession(currentSession)
    setUser(currentSession.user || null)
    return { error: null, session: currentSession }
  }

  /**
   * Sign up with email + password.
   * @returns {{ error: Error | null }}
   */
  const signUp = async (email, password) => {
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) {
      return { error, session: null, needsEmailConfirmation: false }
    }

    const currentSession = data?.session ? await resolveValidSession() : null
    if (currentSession) {
      setSession(currentSession)
      setUser(currentSession.user || null)
      return { error: null, session: currentSession, needsEmailConfirmation: false }
    }

    return { error: null, session: null, needsEmailConfirmation: true }
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
