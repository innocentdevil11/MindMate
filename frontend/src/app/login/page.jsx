'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { motion } from 'framer-motion'

export default function LoginPage() {
  const [isSignUp, setIsSignUp] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(null)

  const { signIn, signUp } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      if (isSignUp) {
        const { error: signUpError } = await signUp(email, password)
        if (signUpError) throw signUpError
        setSuccess('Account created. Redirecting...')
        setTimeout(() => router.push('/'), 500)
      } else {
        const { error: signInError } = await signIn(email, password)
        if (signInError) throw signInError
        router.push('/')
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
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
              {loading ? 'Please wait...' : isSignUp ? 'Create Account' : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="text-center text-slate-400 text-xs mt-4">The same workspace starts here.</p>
      </motion.div>
    </div>
  )
}
