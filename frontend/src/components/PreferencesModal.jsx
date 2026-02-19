'use client'

/**
 * PreferencesModal — MindMate.
 * 
 * Modal for managing user tone preference.
 * Fetches current preference on open, saves on change.
 * 
 * WHY modal instead of page: Preferences are a quick toggle,
 * not a full page experience. A modal keeps the user in context.
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '@/lib/api'

const TONES = [
  { value: 'clean', label: 'Clean', desc: 'Professional and respectful', icon: '✨' },
  { value: 'casual', label: 'Casual', desc: 'Relaxed, like talking to a friend', icon: '💬' },
  { value: 'blunt', label: 'Blunt', desc: 'Direct, no sugar-coating', icon: '🎯' },
  { value: 'blunt_profane', label: 'Blunt + Profanity', desc: 'Raw and unfiltered (opt-in)', icon: '🔥', warning: true },
]

export default function PreferencesModal({ isOpen, onClose }) {
  const [tone, setTone] = useState('clean')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [showProfanityWarning, setShowProfanityWarning] = useState(false)
  const [saved, setSaved] = useState(false)

  // Fetch current preferences when modal opens
  useEffect(() => {
    if (!isOpen) return
    setLoading(true)
    setError(null)
    setSaved(false)
    api.get('/preferences')
      .then(data => {
        setTone(data.tone_preference || 'clean')
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [isOpen])

  const handleToneSelect = async (newTone) => {
    // Show profanity warning if selecting blunt_profane
    if (newTone === 'blunt_profane' && tone !== 'blunt_profane') {
      setShowProfanityWarning(true)
      return
    }
    await saveTone(newTone, false)
  }

  const saveTone = async (newTone, confirmContradiction) => {
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      const result = await api.put('/preferences', {
        tone_preference: newTone,
        confirm_contradiction: confirmContradiction,
      })
      // Handle contradiction response
      if (result.conflict) {
        setError(result.message)
        return
      }
      setTone(newTone)
      setSaved(true)
      setShowProfanityWarning(false)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center px-4"
        onClick={onClose}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ duration: 0.3 }}
          onClick={(e) => e.stopPropagation()}
          className="relative glass rounded-2xl p-6 w-full max-w-md border border-gray-700/50"
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-gray-100 flex items-center gap-2">
              ⚙️ <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">Preferences</span>
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-200 transition-colors text-xl"
            >
              ✕
            </button>
          </div>

          {/* Loading */}
          {loading && (
            <div className="text-center py-8 text-gray-400 text-sm">Loading preferences...</div>
          )}

          {/* Tone Selector */}
          {!loading && (
            <div className="space-y-3">
              <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                Response Tone
              </label>
              {TONES.map((t) => (
                <button
                  key={t.value}
                  onClick={() => handleToneSelect(t.value)}
                  disabled={saving}
                  className={`w-full text-left px-4 py-3 rounded-xl border transition-all duration-200 disabled:opacity-50 ${
                    tone === t.value
                      ? 'bg-violet-500/20 border-violet-500/40 text-violet-300'
                      : 'bg-black/20 border-gray-700/30 text-gray-300 hover:bg-black/30 hover:border-gray-600/40'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{t.icon}</span>
                    <div>
                      <div className="text-sm font-semibold">{t.label}</div>
                      <div className="text-xs text-gray-500">{t.desc}</div>
                    </div>
                    {tone === t.value && (
                      <span className="ml-auto text-violet-400 text-sm">✓</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Profanity Warning */}
          {showProfanityWarning && (
            <div className="mt-4 bg-orange-500/10 border border-orange-500/30 rounded-xl p-4">
              <p className="text-orange-300 text-xs mb-3">
                <strong>⚠️ Explicit Language:</strong> This enables profanity in responses.
                The AI will be raw and unfiltered. No slurs or harassment — just direct language.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => saveTone('blunt_profane', true)}
                  disabled={saving}
                  className="px-4 py-2 bg-orange-500/20 border border-orange-500/30 rounded-lg text-orange-300 text-xs font-semibold hover:bg-orange-500/30 transition-all disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'I understand, enable it'}
                </button>
                <button
                  onClick={() => setShowProfanityWarning(false)}
                  className="px-4 py-2 text-gray-400 text-xs hover:text-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-3 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2 text-red-400 text-xs">
              {error}
            </div>
          )}

          {/* Saved indicator */}
          {saved && (
            <div className="mt-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-3 py-2 text-emerald-400 text-xs">
              ✓ Preferences saved
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
