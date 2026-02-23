'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/lib/api'

export default function FeedbackPanel({ query }) {
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  if (dismissed || submitted) return null

  const submitFeedback = async (isHelpful) => {
    if (submitting) return

    setSubmitting(true)
    try {
      await api.post('/feedback', {
        query,
        usefulness: isHelpful ? 8 : 3,
        tone_alignment: null,
        outcome: isHelpful ? 'helped' : 'didnt_help',
      })
    } catch (err) {
      console.warn('Feedback submission failed:', err.message)
    } finally {
      setSubmitting(false)
      setSubmitted(true)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex items-center gap-2 flex-wrap"
    >
      <span className="text-xs text-slate-400">Helpful?</span>
      <button
        onClick={() => submitFeedback(true)}
        disabled={submitting}
        className="px-2.5 py-1 rounded-full text-xs bg-white border border-slate-200 text-slate-600 hover:border-slate-300 disabled:opacity-50"
      >
        Helpful
      </button>
      <button
        onClick={() => submitFeedback(false)}
        disabled={submitting}
        className="px-2.5 py-1 rounded-full text-xs bg-white border border-slate-200 text-slate-600 hover:border-slate-300 disabled:opacity-50"
      >
        Not helpful
      </button>
      <button
        onClick={() => setDismissed(true)}
        className="text-xs text-slate-400 hover:text-slate-600"
      >
        Dismiss
      </button>
    </motion.div>
  )
}
