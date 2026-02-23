'use client'

import { useEffect, useRef, useState } from 'react'

export default function AudioRecorder({ onTranscription, isLoading }) {
  const [isListening, setIsListening] = useState(false)
  const [isSupported] = useState(() => {
    if (typeof window === 'undefined') return true
    return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
  })

  const recognitionRef = useRef(null)

  useEffect(() => {
    if (!isSupported) return

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'en-US'

    recognition.onresult = (event) => {
      const finalText = Array.from(event.results)
        .map((result) => result[0]?.transcript || '')
        .join(' ')
        .trim()

      if (finalText) onTranscription(finalText)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.onerror = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition

    return () => {
      recognition.abort()
    }
  }, [isSupported, onTranscription])

  const startListening = (e) => {
    if (e) e.preventDefault()
    if (!recognitionRef.current || isLoading || isListening) return

    try {
      recognitionRef.current.start()
      setIsListening(true)
    } catch {
      setIsListening(false)
    }
  }

  const stopListening = (e) => {
    if (e) e.preventDefault()
    if (!recognitionRef.current || !isListening) return

    try {
      recognitionRef.current.stop()
    } catch {
      setIsListening(false)
    }
  }

  if (!isSupported) return null

  return (
    <button
      type="button"
      onMouseDown={startListening}
      onMouseUp={stopListening}
      onMouseLeave={stopListening}
      onTouchStart={startListening}
      onTouchEnd={stopListening}
      onTouchCancel={stopListening}
      onKeyDown={(e) => {
        if (e.key === ' ' || e.key === 'Enter') startListening(e)
      }}
      onKeyUp={(e) => {
        if (e.key === ' ' || e.key === 'Enter') stopListening(e)
      }}
      disabled={isLoading}
      aria-pressed={isListening}
      aria-label={isListening ? 'Listening, release to stop' : 'Hold to talk'}
      title={isListening ? 'Listening, release to stop' : 'Hold to talk'}
      className={`w-10 h-10 rounded-full border flex items-center justify-center transition-colors ${
        isListening
          ? 'bg-emerald-100 border-emerald-200 text-emerald-700'
          : 'bg-slate-100 border-slate-200 text-slate-500 hover:bg-slate-200'
      } disabled:opacity-50`}
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
      </svg>
    </button>
  )
}
