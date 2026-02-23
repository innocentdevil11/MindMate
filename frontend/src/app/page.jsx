'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Settings, Send, Mic, X } from 'lucide-react'
import WeightSlider from '@/components/WeightSlider'
import AgentCard from '@/components/AgentCard'
import MarkdownRenderer from '@/components/MarkdownRenderer'
import Blob from '@/components/Blob'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import FeedbackPanel from '@/components/FeedbackPanel'
import ExplanationPanel from '@/components/ExplanationPanel'

const agentConfig = [
  { key: 'ethical', label: 'Ethical', descriptor: 'Moral and philosophical perspective', color: 'violet' },
  { key: 'risk', label: 'Risk and Logic', descriptor: 'Analytical risk assessment', color: 'orange' },
  { key: 'eq', label: 'EQ', descriptor: 'Emotional intelligence lens', color: 'pink' },
  { key: 'values', label: 'Value Alignment', descriptor: 'Personal values harmony', color: 'emerald' },
  { key: 'red_team', label: 'Red Team', descriptor: 'Devils advocate perspective', color: 'cyan' },
]

const TONE_OPTIONS = [
  { value: 'clean', label: 'Clean' },
  { value: 'casual', label: 'Casual' },
  { value: 'blunt', label: 'Blunt' },
  { value: 'blunt_profane', label: 'Unfiltered' },
]

const TONE_LABELS = {
  clean: 'Clean',
  casual: 'Casual',
  blunt: 'Blunt',
  blunt_profane: 'Unfiltered',
}

export default function Home() {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([])
  const [weights, setWeights] = useState({
    ethical: 0.2,
    risk: 0.2,
    eq: 0.2,
    values: 0.2,
    red_team: 0.2,
  })

  const [isVoiceMode, setIsVoiceMode] = useState(false)
  const [isVoiceListening, setIsVoiceListening] = useState(false)
  const [voiceDraft, setVoiceDraft] = useState('')
  const [voiceInterim, setVoiceInterim] = useState('')

  const [showSettings, setShowSettings] = useState(false)
  const [expandedInsights, setExpandedInsights] = useState({})
  const [isInputFocused, setIsInputFocused] = useState(false)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const { user, loading: authLoading, signOut } = useAuth()
  const router = useRouter()
  const messagesEndRef = useRef(null)
  const queryInputRef = useRef(null)

  const [currentTone, setCurrentTone] = useState('clean')
  const [toneSaving, setToneSaving] = useState(false)

  const [isVoiceSupported] = useState(() => {
    if (typeof window === 'undefined') return true
    return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
  })
  const voiceRecognitionRef = useRef(null)

  const hasMessages = messages.length > 0
  const isComposing = isInputFocused || query.length > 0

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (!user) return
    api
      .get('/preferences')
      .then((data) => setCurrentTone(data.tone_preference || 'clean'))
      .catch(() => {})
  }, [user])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    const textarea = queryInputRef.current
    if (!textarea) return

    textarea.style.height = '0px'
    const maxHeight = 160
    const nextHeight = Math.min(textarea.scrollHeight, maxHeight)
    textarea.style.height = `${nextHeight}px`
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [query])

  useEffect(() => {
    if (!isVoiceSupported) return

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event) => {
      let finalText = ''
      let interim = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalText += transcript
        } else {
          interim += transcript
        }
      }

      setVoiceInterim(interim)

      if (finalText.trim()) {
        setVoiceDraft((prev) => (prev ? `${prev} ${finalText.trim()}` : finalText.trim()))
      }
    }

    recognition.onend = () => {
      setIsVoiceListening(false)
      setVoiceInterim('')
    }

    recognition.onerror = () => {
      setIsVoiceListening(false)
      setVoiceInterim('')
    }

    voiceRecognitionRef.current = recognition

    return () => {
      recognition.abort()
    }
  }, [isVoiceSupported])

  const startVoiceCapture = () => {
    if (!voiceRecognitionRef.current || loading || isVoiceListening) return
    try {
      setVoiceInterim('')
      voiceRecognitionRef.current.start()
      setIsVoiceListening(true)
    } catch {
      setIsVoiceListening(false)
    }
  }

  const stopVoiceCapture = () => {
    if (!voiceRecognitionRef.current || !isVoiceListening) return
    try {
      voiceRecognitionRef.current.stop()
    } catch {
      setIsVoiceListening(false)
    }
  }

  const submitDecision = async (rawText) => {
    const text = rawText.trim()
    if (!text) return

    const userMessage = { id: Date.now(), role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)
    setError(null)

    try {
      const data = await api.post('/decision', {
        query: text,
        weights,
      })
      setMessages((prev) => [...prev, { id: Date.now() + 1, role: 'assistant', data, query: text }])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    if (e) e.preventDefault()
    const currentQuery = query.trim()
    if (!currentQuery) return
    setQuery('')
    await submitDecision(currentQuery)
  }

  const handleVoiceSubmit = async () => {
    const spokenText = voiceDraft.trim()
    if (!spokenText || loading) return

    stopVoiceCapture()
    setIsVoiceMode(false)
    setVoiceInterim('')
    setVoiceDraft('')
    await submitDecision(spokenText)
  }

  const handleQueryKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const updateWeight = (key, value) => {
    setWeights((prev) => ({ ...prev, [key]: value }))
  }

  const saveTone = async (newTone) => {
    const previousTone = currentTone
    setCurrentTone(newTone)
    setToneSaving(true)
    try {
      await api.put('/preferences', {
        tone_preference: newTone,
        confirm_contradiction: true,
      })
    } catch (err) {
      console.warn('Failed to save tone:', err.message)
      setCurrentTone(previousTone)
    } finally {
      setToneSaving(false)
    }
  }

  const handleToneSelect = async (newTone) => {
    if (newTone === currentTone) return
    await saveTone(newTone)
  }

  const toggleInsights = (msgId) => {
    setExpandedInsights((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }))
  }

  const getMessageOpacity = (index) => {
    const age = messages.length - index - 1
    if (age >= 4) return 0.58
    if (age === 3) return 0.7
    if (age === 2) return 0.82
    if (age === 1) return 0.92
    return 1
  }

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-[#F6F6F8] flex items-center justify-center">
        <div className="text-slate-400 text-sm">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex justify-center bg-[radial-gradient(ellipse_at_top_left,_#e9e4f6_0%,_transparent_55%),radial-gradient(ellipse_at_top_right,_#e8f4ef_0%,_transparent_45%),radial-gradient(ellipse_at_bottom,_#f3e8f5_0%,_#f8f8fa_58%)]">
      <AnimatePresence>
        {isVoiceMode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-[#F7F6F7]/95 backdrop-blur-sm flex items-center justify-center px-4"
          >
            <div className="w-full max-w-md rounded-[2.2rem] bg-white/92 border border-white/80 shadow-[0_20px_50px_rgba(15,23,42,0.10)] p-7 sm:p-8">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">Voice Mode</p>
                  <h2 className="text-2xl font-medium text-slate-700 mt-2">Talk through your thought</h2>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setIsVoiceMode(false)
                    stopVoiceCapture()
                  }}
                  className="p-2 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                  aria-label="Close voice mode"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="my-7 flex justify-center">
                <Blob isListening={isVoiceListening} tone={currentTone} size="lg" />
              </div>

              <p className="text-sm text-slate-500 text-center">
                {!isVoiceSupported
                  ? 'Voice input is unavailable in this browser.'
                  : isVoiceListening
                    ? 'Listening... release to stop'
                    : 'Push and hold to talk'}
              </p>

              <div className="mt-4 flex justify-center">
                <button
                  type="button"
                  onMouseDown={startVoiceCapture}
                  onMouseUp={stopVoiceCapture}
                  onMouseLeave={stopVoiceCapture}
                  onTouchStart={startVoiceCapture}
                  onTouchEnd={stopVoiceCapture}
                  onTouchCancel={stopVoiceCapture}
                  disabled={!isVoiceSupported || loading}
                  className={`w-16 h-16 rounded-full flex items-center justify-center border transition-colors ${
                    isVoiceListening
                      ? 'bg-emerald-100 border-emerald-200 text-emerald-700'
                      : 'bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200'
                  } disabled:opacity-50`}
                  aria-label="Hold to talk"
                >
                  <Mic className="w-6 h-6" />
                </button>
              </div>

              <div className="mt-5 rounded-2xl border border-slate-200 bg-white/95 p-4 min-h-28 max-h-48 overflow-y-auto">
                {voiceDraft || voiceInterim ? (
                  <p className="text-sm text-slate-700 leading-7 whitespace-pre-wrap">
                    {voiceDraft}
                    {voiceInterim ? <span className="text-slate-400 italic"> {voiceInterim}</span> : null}
                  </p>
                ) : (
                  <p className="text-sm text-slate-400">Start speaking and your transcript will appear here.</p>
                )}
              </div>

              <div className="mt-4 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setVoiceDraft('')
                    setVoiceInterim('')
                  }}
                  className="px-3 py-2 rounded-lg text-sm text-slate-500 hover:text-slate-700"
                >
                  Clear
                </button>
                <button
                  type="button"
                  onClick={handleVoiceSubmit}
                  disabled={loading || !voiceDraft.trim()}
                  className="px-4 py-2 rounded-xl bg-slate-700 text-white text-sm hover:bg-slate-800 disabled:bg-slate-200 disabled:text-slate-400"
                >
                  Send to MindMate
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="w-full max-w-[900px] h-screen px-3 sm:px-6 py-3 sm:py-5">
        <div className="h-full rounded-[2rem] sm:rounded-[2.3rem] border border-white/70 bg-white/70 backdrop-blur-sm shadow-[0_18px_50px_rgba(15,23,42,0.08)] flex flex-col overflow-hidden">
          <header className="flex-none px-4 sm:px-6 pt-4 sm:pt-5 pb-3 flex items-center justify-between border-b border-slate-200/60">
            <div>
              <p className="text-[11px] uppercase tracking-[0.17em] text-slate-400">MindMate</p>
              <h1 className="text-sm sm:text-base text-slate-600 mt-1">Calm thinking workspace</h1>
            </div>

            <div className="flex items-center gap-1.5 sm:gap-2">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className={`p-2 rounded-full transition-colors ${
                  showSettings ? 'bg-slate-200/80 text-slate-700' : 'text-slate-400 hover:bg-slate-100'
                }`}
                aria-label="Toggle settings"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </header>

          <AnimatePresence>
            {showSettings && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden bg-white/80 border-b border-slate-200/60"
              >
                <div className="px-4 sm:px-6 py-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-medium text-slate-600">Agent Influence</h3>
                    <button onClick={signOut} className="text-xs text-slate-500 hover:text-slate-700">
                      Sign out
                    </button>
                  </div>
                  <div className="flex flex-col gap-4">
                    {agentConfig.map((agent) => (
                      <WeightSlider
                        key={agent.key}
                        label={agent.label}
                        value={weights[agent.key]}
                        onChange={(val) => updateWeight(agent.key, val)}
                        color={agent.color}
                        disabled={loading}
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <main className="flex-1 overflow-y-auto px-4 sm:px-6 pt-5 pb-3">
            <AnimatePresence mode="popLayout">
              {!hasMessages ? (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: isComposing ? -8 : 0 }}
                  exit={{ opacity: 0, y: -16 }}
                  transition={{ duration: 0.35 }}
                  className="min-h-[50vh] flex flex-col items-center justify-center text-center"
                >
                  <div className="mb-5">
                    <Blob tone={currentTone} size="md" />
                  </div>
                  <h2 className="text-xl sm:text-2xl font-medium text-slate-700">A quiet place to think</h2>
                  <p className="text-sm sm:text-base text-slate-500 mt-2 max-w-md">
                    Start typing below. Your conversation builds here naturally.
                  </p>
                </motion.div>
              ) : (
                <div className="mx-auto w-full max-w-[680px] flex flex-col gap-9 sm:gap-11 pb-3">
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={msg.id}
                      layout="position"
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: getMessageOpacity(idx), y: 0 }}
                      transition={{ duration: 0.32 }}
                      className={`w-full flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {msg.role === 'user' ? (
                        <div className="max-w-[88%] rounded-[1.5rem] rounded-tr-lg px-4 sm:px-5 py-3.5 bg-slate-700 text-white">
                          <p className="text-[15px] sm:text-base leading-7 whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      ) : (
                        <div className="w-full max-w-[92%]">
                          <div className="rounded-[1.55rem] rounded-tl-lg px-4 sm:px-5 py-4 bg-[#ffffff] border border-slate-200/90 shadow-[0_8px_24px_rgba(15,23,42,0.08)]">
                            <MarkdownRenderer content={msg.data.final_decision} className="text-slate-800" />
                          </div>

                          <div className="mt-3 flex items-center gap-3">
                            <button
                              onClick={() => toggleInsights(msg.id)}
                              className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
                            >
                              {expandedInsights[msg.id] ? 'Hide details' : 'See details'}
                            </button>
                          </div>

                          <AnimatePresence>
                            {expandedInsights[msg.id] && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.25 }}
                                className="overflow-hidden mt-3 flex flex-col gap-3"
                              >
                                {agentConfig.map((agent, agentIdx) => (
                                  <AgentCard
                                    key={agent.key}
                                    name={agent.label}
                                    descriptor={agent.descriptor}
                                    output={msg.data.agent_outputs[agent.key]}
                                    color={agent.color}
                                    delay={agentIdx * 0.06}
                                  />
                                ))}
                                <ExplanationPanel explanation={msg.data.explanation} />
                              </motion.div>
                            )}
                          </AnimatePresence>

                          <div className="mt-3">
                            <FeedbackPanel query={msg.query} />
                          </div>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </AnimatePresence>

            {loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto w-full max-w-[680px] pt-3 flex items-center gap-3 text-slate-500">
                <Blob tone={currentTone} size="xs" isThinking />
                <span className="text-sm">MindMate is thinking...</span>
              </motion.div>
            )}

            {error && (
              <div className="mx-auto w-full max-w-[680px] mt-3 p-3 rounded-xl bg-red-50 border border-red-100 text-red-500 text-sm">
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </main>

          <footer className="px-4 sm:px-6 pt-2 pb-4 sm:pb-5">
            <div className="mx-auto w-full max-w-[680px]">
              <form
                onSubmit={handleSubmit}
                className={`flex items-end gap-2 sm:gap-3 rounded-[1.8rem] border px-3 sm:px-4 py-2.5 bg-white/92 transition-shadow ${
                  isComposing ? 'border-slate-300 shadow-[0_10px_28px_rgba(15,23,42,0.10)]' : 'border-slate-200 shadow-sm'
                }`}
              >
                <div className="relative group shrink-0">
                  <button
                    type="button"
                    onClick={() => setIsVoiceMode(true)}
                    className="w-10 h-10 rounded-full flex items-center justify-center text-slate-500 hover:text-slate-700 hover:bg-slate-100"
                    aria-label="Switch to voice mode"
                    title="Switch to voice mode"
                  >
                    <Mic className="w-5 h-5" />
                  </button>
                  <div className="pointer-events-none absolute -top-11 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-slate-800 px-2.5 py-1 text-[11px] text-white opacity-0 group-hover:opacity-100 transition-opacity">
                    Switch to voice mode
                  </div>
                </div>

                <textarea
                  ref={queryInputRef}
                  rows={1}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleQueryKeyDown}
                  onFocus={() => setIsInputFocused(true)}
                  onBlur={() => setIsInputFocused(false)}
                  disabled={loading}
                  placeholder="What are you thinking through right now?"
                  className="chat-input-scroll flex-1 bg-transparent border-none outline-none text-slate-700 text-[15px] sm:text-base placeholder:text-slate-400 resize-none max-h-40 leading-6 py-1"
                />

                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="w-10 h-10 rounded-full bg-slate-700 text-white flex items-center justify-center hover:bg-slate-800 disabled:bg-slate-200 disabled:opacity-60"
                  aria-label="Send message"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>

              <div className="mt-2.5 flex flex-wrap items-center justify-center gap-1.5">
                {TONE_OPTIONS.map((tone) => (
                  <button
                    key={tone.value}
                    type="button"
                    onClick={() => handleToneSelect(tone.value)}
                    disabled={toneSaving}
                    className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
                      currentTone === tone.value
                        ? 'bg-slate-700 border-slate-700 text-white'
                        : 'bg-white/90 border-slate-200 text-slate-600 hover:border-slate-300'
                    } disabled:opacity-60`}
                  >
                    {tone.label}
                  </button>
                ))}
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  )
}
