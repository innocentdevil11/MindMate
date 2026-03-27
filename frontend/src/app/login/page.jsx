'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { motion } from 'framer-motion'
import { API_URL } from '@/lib/api'

export default function LoginPage() {
  const [isSignUp, setIsSignUp] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(null)
  const [statusMessage, setStatusMessage] = useState(null)

  const { signIn, signUp } = useAuth()
  const router = useRouter()
  const apiBase = API_URL

  const getAuthErrorMessage = (err, signUpMode) => {
    const raw = err?.message || ''
    const message = raw.toLowerCase()

    if (signUpMode && message.includes('already registered')) {
      return 'This email is already registered. Please switch to Sign In.'
    }
    if (message.includes('invalid email')) {
      return 'Please enter a valid email address.'
    }
    if (message.includes('password')) {
      return raw || 'Password does not meet the project auth policy.'
    }
    if (err?.status === 422) {
      return 'Signup details were rejected. Check email/password and try again.'
    }
    return raw || 'Something went wrong'
  }

  const ensureBackendAcceptsSession = async (session) => {
    const token = session?.access_token
    if (!token) throw new Error('Missing access token after sign-in.')

    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      setStatusMessage('Waking up the server (this can take up to 50s)...')
    }, 3000)

    try {
      const response = await fetch(`${apiBase}/conversations`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        signal: controller.signal
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Backend auth check failed (${response.status})`)
      }
    } finally {
      clearTimeout(timeoutId)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setStatusMessage(null)
    setLoading(true)

    const cleanEmail = email.trim().toLowerCase()
    const cleanPassword = password.trim()

    try {
      if (isSignUp) {
        const { error: signUpError, session: signUpSession, needsEmailConfirmation } = await signUp(cleanEmail, cleanPassword)
        if (signUpError) throw signUpError
        if (signUpSession) {
          await ensureBackendAcceptsSession(signUpSession)
          setSuccess('Account created. Redirecting...')
          setTimeout(() => router.push('/'), 500)
          return
        }
        if (needsEmailConfirmation) {
          setSuccess('Account created. Check your email for a verification link, then sign in.')
          setIsSignUp(false)
          return
        }
        setSuccess('Account created. Please sign in.')
        setIsSignUp(false)
      } else {
        const { error: signInError, session: signInSession } = await signIn(cleanEmail, cleanPassword)
        if (signInError) throw signInError
        if (!signInSession) {
          throw new Error('No active session. Please sign in again.')
        }
        
        // Wait for Render cold start logic
        await ensureBackendAcceptsSession(signInSession)
        router.push('/')
      }
    } catch (err) {
      setError(getAuthErrorMessage(err, isSignUp))
    } finally {
      setLoading(false)
      setStatusMessage(null)
    }
  }

  return (
    <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center px-4 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-7">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">MindMate</p>
          <h1 className="text-2xl font-medium text-slate-700 mt-2 tracking-tight">Continue your thinking session</h1>
          <p className="text-slate-500 text-sm mt-2">Sign in to return to your workspace.</p>
        </div>

        <div className="rounded-[1.75rem] bg-white/90 border border-slate-200/80 shadow-[0_12px_36px_rgba(15,23,42,0.08)] p-6 sm:p-7">
          <div className="flex mb-6 bg-slate-100/80 rounded-2xl p-1">
            <button
              onClick={() => {
                setIsSignUp(false)
                setError(null)
                setSuccess(null)
              }}
              className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                !isSignUp ? 'bg-white text-slate-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setIsSignUp(true)
                setError(null)
                setSuccess(null)
              }}
              className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                isSignUp ? 'bg-white text-slate-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 uppercase tracking-[0.16em]">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
                placeholder="you@example.com"
                className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-300 focus:border-slate-300 transition-colors disabled:opacity-50 text-sm"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 uppercase tracking-[0.16em]">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                minLength={6}
                placeholder="At least 6 characters"
                className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-300 focus:border-slate-300 transition-colors disabled:opacity-50 text-sm"
              />
            </div>

            {error && <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-2.5 text-red-500 text-xs">{error}</div>}

            {success && (
              <div className="bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-2.5 text-emerald-600 text-xs">
                {success}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-slate-700 rounded-xl font-semibold text-white text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors hover:bg-slate-800"
            >
              {loading ? (statusMessage || 'Please wait...') : (isSignUp ? 'Create Account' : 'Sign In')}
            </button>
          </form>
        </div>

        <p className="text-center text-slate-400 text-xs mt-4">The same workspace starts here.</p>
      </motion.div>
    </div>
  )
}

