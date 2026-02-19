'use client'

/**
 * FeedbackPanel — MindMate.
 * 
 * Appears below the decision result. Optional — does not block chat.
 * Collects usefulness rating + tone alignment feedback.
 * 
 * WHY optional: Forcing feedback kills engagement.
 * This panel is dismissable and non-intrusive.
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/lib/api'

const TONE_OPTIONS = [
  { value: 'too_soft', label: '😊 Too Soft' },
  { value: 'just_right', label: '👌 Just Right' },
  { value: 'too_harsh', label: '😤 Too Harsh' },
]

export default function FeedbackPanel({ query }) {
  const [usefulness, setUsefulness] = useState(null)
  const [toneAlignment, setToneAlignment] = useState(null)
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  if (dismissed || submitted) return null

  const handleSubmit = async () => {
    if (!usefulness && !toneAlignment) return
    setSubmitting(true)
    try {
      await api.post('/feedback', {
        query,
        usefulness,
        tone_alignment: toneAlignment,
        outcome: usefulness && usefulness >= 6 ? 'helped' : usefulness ? 'didnt_help' : null,
      })
      setSubmitted(true)
    } catch (err) {
      // Silently fail — feedback is optional
      console.warn('Feedback submission failed:', err.message)
      setSubmitted(true)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 1.2 }}
      className="glass rounded-xl p-5 border border-gray-700/30 mt-6"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          Was this helpful?
        </span>
        <button
          onClick={() => setDismissed(true)}
          className="text-gray-500 hover:text-gray-300 text-xs"
        >
          Dismiss
        </button>
      </div>

      {/* Usefulness slider */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-gray-500">Usefulness</span>
          <span className="text-xs text-gray-400 font-mono">
            {usefulness ? `${usefulness}/10` : '—'}
          </span>
        </div>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
            <button
              key={n}
              onClick={() => setUsefulness(n)}
              className={`flex-1 py-1.5 rounded text-xs font-semibold transition-all duration-150 ${
                usefulness === n
                  ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-500/40'
                  : usefulness && n <= usefulness
                    ? 'bg-cyan-500/10 text-cyan-400/60'
                    : 'bg-black/20 text-gray-500 hover:bg-black/30 hover:text-gray-400'
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {/* Tone alignment */}
      <div className="mb-4">
        <span className="text-xs text-gray-500 block mb-1.5">Tone</span>
        <div className="flex gap-2">
          {TONE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setToneAlignment(opt.value)}
              className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all duration-150 ${
                toneAlignment === opt.value
                  ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                  : 'bg-black/20 text-gray-400 hover:bg-black/30 border border-transparent'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={submitting || (!usefulness && !toneAlignment)}
        className="w-full py-2 bg-gradient-to-r from-cyan-500/20 to-violet-500/20 border border-cyan-500/20 rounded-lg text-sm text-gray-300 font-semibold disabled:opacity-30 disabled:cursor-not-allowed hover:border-cyan-500/40 transition-all duration-200"
      >
        {submitting ? 'Sending...' : 'Submit Feedback'}
      </button>
    </motion.div>
  )
}
