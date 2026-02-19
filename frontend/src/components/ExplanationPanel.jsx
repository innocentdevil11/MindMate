'use client'

/**
 * ExplanationPanel — MindMate (DEV-ONLY).
 * 
 * Collapsible panel showing backend explanation metadata.
 * Only visible when NEXT_PUBLIC_DEV_MODE=true.
 * 
 * WHY dev-only: End users don't need to see confidence scores
 * or memory labels. This is for debugging and trust building
 * during development.
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const IS_DEV = process.env.NEXT_PUBLIC_DEV_MODE === 'true'

export default function ExplanationPanel({ explanation }) {
  const [isOpen, setIsOpen] = useState(false)

  // Only render in dev mode and if explanation data exists
  if (!IS_DEV || !explanation) return null

  return (
    <div className="mt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-xs text-gray-500 hover:text-gray-400 font-mono flex items-center gap-1 transition-colors"
      >
        <span>{isOpen ? '▼' : '▶'}</span>
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
            <div className="mt-2 bg-black/40 border border-gray-700/30 rounded-lg p-3 font-mono text-xs text-gray-400 space-y-1">
              <div>
                <span className="text-gray-500">tone_mode:</span>{' '}
                <span className="text-cyan-400">{explanation.tone_mode}</span>
              </div>
              <div>
                <span className="text-gray-500">memory_labels:</span>{' '}
                <span className="text-violet-400">
                  {explanation.memory_labels_used?.length
                    ? explanation.memory_labels_used.join(', ')
                    : 'none'}
                </span>
              </div>
              <div>
                <span className="text-gray-500">has_memory:</span>{' '}
                <span className={explanation.has_memory_context ? 'text-emerald-400' : 'text-gray-500'}>
                  {String(explanation.has_memory_context)}
                </span>
              </div>
              <div>
                <span className="text-gray-500">confidence:</span>{' '}
                <span className={explanation.response_confidence >= 0.8 ? 'text-emerald-400' : 'text-orange-400'}>
                  {(explanation.response_confidence * 100).toFixed(0)}%
                </span>
              </div>
              {explanation.preference_confidence !== undefined && (
                <div>
                  <span className="text-gray-500">pref_confidence:</span>{' '}
                  <span className="text-gray-400">
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
