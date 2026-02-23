'use client'

/**
 * ExplanationPanel — MindMate (Calm Redesign, DEV-ONLY)
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight, ChevronDown } from 'lucide-react'

const IS_DEV = process.env.NEXT_PUBLIC_DEV_MODE === 'true'

export default function ExplanationPanel({ explanation }) {
  const [isOpen, setIsOpen] = useState(false)

  if (!IS_DEV || !explanation) return null

  return (
    <div className="mt-4 border-t border-slate-100 pt-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-xs text-slate-400 hover:text-slate-600 font-mono flex items-center gap-1 transition-colors"
      >
        {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        <span>Debug: Explanation Metadata</span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-2 bg-slate-50 border border-slate-100 rounded-lg p-3 font-mono text-[11px] text-slate-500 space-y-1.5 shadow-inner">
              <div className="flex justify-between">
                <span className="text-slate-400">tone_mode:</span>
                <span className="text-indigo-500 font-semibold">{explanation.tone_mode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">memory_labels:</span>
                <span className="text-violet-500 font-semibold text-right max-w-[150px] truncate">
                  {explanation.memory_labels_used?.length
                    ? explanation.memory_labels_used.join(', ')
                    : 'none'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">has_memory:</span>
                <span className={explanation.has_memory_context ? 'text-emerald-500 font-semibold' : 'text-slate-400'}>
                  {String(explanation.has_memory_context)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">confidence:</span>
                <span className={explanation.response_confidence >= 0.8 ? 'text-emerald-500 font-semibold' : 'text-orange-500 font-semibold'}>
                  {(explanation.response_confidence * 100).toFixed(0)}%
                </span>
              </div>
              {explanation.preference_confidence !== undefined && (
                <div className="flex justify-between">
                  <span className="text-slate-400">pref_confidence:</span>
                  <span className="text-slate-600 font-semibold">
                    {(explanation.preference_confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
