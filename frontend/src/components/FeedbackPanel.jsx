'use client'

/**
 * FeedbackPanel — MindMate v3
 *
 * Submits structured feedback with conversation/message IDs
 * and brain config snapshot for brain evolution.
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/lib/api'
import { Star } from 'lucide-react'

export default function FeedbackPanel({ conversationId, messageId, brainConfig }) {
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [dismissed, setDismissed] = useState(false)
  const [evolution, setEvolution] = useState(null)

  const [rating, setRating] = useState(null)
  const [textFeedback, setTextFeedback] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)

  // Removed FEEDBACK_OPTIONS as the user specifically requested 1-10 and a text box

  if (dismissed || submitted) {
    if (submitted && evolution?.evolution_triggered) {
      return (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-1.5"
        >
          <span className="text-[11px] text-emerald-500">✨ Brain evolved based on your feedback</span>
        </motion.div>
      )
    }
    return null
  }

  const submitFeedback = async () => {
    if (submitting || !conversationId || !messageId || !rating) return

    setSubmitting(true)
    try {
      const typeToSubmit = rating >= 7 ? 'thumbs_up' : 'thumbs_down'
      const result = await api.post('/feedback', {
        conversation_id: conversationId,
        message_id: messageId,
        rating: rating,
        feedback_type: typeToSubmit,
        text_feedback: textFeedback.trim() || undefined,
        brain_config: brainConfig || null,
      })
      setEvolution(result)
    } catch (err) {
      console.warn('Feedback submission failed:', err.message)
    } finally {
      setSubmitting(false)
      setSubmitted(true)
    }
  }

  return (
    <div className="mt-2 w-full max-w-md">
      {!isExpanded ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-wrap gap-2"
        >
          <button
            onClick={() => setIsExpanded(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-slate-200 bg-white text-xs font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors"
          >
            <Star className="w-3.5 h-3.5" />
            Provide Feedback
          </button>
        </motion.div>
      ) : !rating ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="flex flex-col gap-2"
        >
          <div className="flex items-center justify-between px-1">
            <span className="text-xs text-slate-500 font-medium">Rate this response</span>
            <button
              onClick={() => {
                setIsExpanded(false)
                setDismissed(true)
              }}
              className="text-[10px] text-slate-400 hover:text-slate-600"
            >
              Dismiss
            </button>
          </div>
          <div className="flex items-center gap-1 flex-wrap">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
              <button
                key={num}
                onClick={() => setRating(num)}
                className="w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-md text-xs font-medium bg-white border border-slate-200 text-slate-600 hover:border-slate-400 hover:bg-slate-50 transition-colors"
              >
                {num}
              </button>
            ))}
          </div>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="p-4 rounded-xl md:rounded-2xl bg-slate-50 border border-slate-200"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-slate-700">How would you like the output to be?</p>
            <span className="text-[10px] font-semibold text-slate-400 bg-slate-200 px-2 py-0.5 rounded-full">{rating} / 10</span>
          </div>

          <textarea
            value={textFeedback}
            onChange={(e) => setTextFeedback(e.target.value)}
            placeholder="Tell me how to improve this response..."
            className="w-full text-sm text-slate-700 p-3 rounded-lg border border-slate-200 bg-white resize-none h-20 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />

          <div className="flex items-center justify-between mt-3">
            <button
              onClick={submitFeedback}
              disabled={submitting}
              className="px-4 py-2 rounded-lg text-xs font-medium bg-slate-800 text-white hover:bg-slate-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
            <button
              onClick={() => { setRating(null); setIsExpanded(false); setTextFeedback(''); }}
              disabled={submitting}
              className="px-3 py-2 rounded-lg text-xs font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-200/50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </motion.div>
      )}
    </div>
  )
}
