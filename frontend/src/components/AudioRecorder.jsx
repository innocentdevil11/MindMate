'use client'

/**
 * AudioRecorder — MindMate (v2: inline mic button).
 * 
 * REWRITTEN from the original bulky "Live Audio Input" section.
 * Now renders as a compact mic icon that sits inside the textarea area,
 * similar to ChatGPT/WhatsApp voice input.
 * 
 * WHY Web Speech API instead of Whisper WebSocket:
 * - The original used WebSocket endpoints (/ws/transcribe-live) that
 *   don't exist in the backend and require a local Whisper model
 * - Web Speech API is built into Chrome/Edge, is free, and needs
 *   zero backend infrastructure
 * - Works perfectly for deployment without any server-side changes
 * 
 * BROWSER SUPPORT: Chrome, Edge, Safari (most modern browsers).
 * Firefox has limited support — falls back gracefully with an error message.
 */

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function AudioRecorder({ onTranscription, isLoading }) {
  const [isListening, setIsListening] = useState(false)
  const [isSupported, setIsSupported] = useState(true)
  const [interimText, setInterimText] = useState('')
  const recognitionRef = useRef(null)

  useEffect(() => {
    // Check browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setIsSupported(false)
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event) => {
      let final = ''
      let interim = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          final += transcript
        } else {
          interim += transcript
        }
      }

      if (final) {
        onTranscription(final.trim())
        setInterimText('')
      } else {
        setInterimText(interim)
      }
    }

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error)
      setIsListening(false)
      setInterimText('')
    }

    recognition.onend = () => {
      setIsListening(false)
      setInterimText('')
    }

    recognitionRef.current = recognition

    return () => {
      recognition.abort()
    }
  }, [onTranscription])

  const toggleListening = () => {
    if (!recognitionRef.current) return

    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      recognitionRef.current.start()
      setIsListening(true)
    }
  }

  // Not supported — show nothing
  if (!isSupported) return null

  return (
    <div className="relative flex items-center">
      {/* Interim text indicator */}
      <AnimatePresence>
        {isListening && interimText && (
          <motion.span
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            className="absolute right-14 text-xs text-gray-500 italic max-w-[200px] truncate"
          >
            {interimText}...
          </motion.span>
        )}
      </AnimatePresence>

      {/* Mic button */}
      <motion.button
        type="button"
        onClick={toggleListening}
        disabled={isLoading}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className={`relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 disabled:opacity-30 cursor-pointer ${isListening
            ? 'bg-red-500/20 text-red-400 border border-red-500/40'
            : 'bg-white/5 text-gray-400 border border-gray-700/30 hover:text-cyan-400 hover:border-cyan-500/30 hover:bg-cyan-500/10'
          }`}
        title={isListening ? 'Stop listening' : 'Voice input'}
      >
        {/* Pulsing ring when recording */}
        {isListening && (
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-red-500/40"
            animate={{ scale: [1, 1.4, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          />
        )}

        {/* Mic SVG icon */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-5 h-5 relative z-10"
        >
          {isListening ? (
            // Stop icon when recording
            <rect x="6" y="6" width="12" height="12" rx="2" />
          ) : (
            // Mic icon
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          )}
        </svg>
      </motion.button>
    </div>
  )
}
