'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Settings, Send, Mic, Plus, Menu, Edit3, AlignJustify, X } from 'lucide-react'
import WeightSlider from '@/components/WeightSlider'
import MarkdownRenderer from '@/components/MarkdownRenderer'
import Blob from '@/components/Blob'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import FeedbackPanel from '@/components/FeedbackPanel'

const agentConfig = [
  { key: 'ethical', label: 'Ethical', descriptor: 'Moral and philosophical perspective', color: 'violet' },
  { key: 'analytical', label: 'Analytical', descriptor: 'Logic and risk assessment', color: 'orange' },
  { key: 'emotional', label: 'Emotional', descriptor: 'Emotional intelligence lens', color: 'pink' },
  { key: 'values', label: 'Values', descriptor: 'Personal values harmony', color: 'emerald' },
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
  const [conversationId, setConversationId] = useState(null)
  const [conversations, setConversations] = useState([])
  const [conversationsLoading, setConversationsLoading] = useState(false)
  const [conversationError, setConversationError] = useState(null)
  const [showComposerExtras, setShowComposerExtras] = useState(false)
  const [showSidebar, setShowSidebar] = useState(false)
  const [renameDraftId, setRenameDraftId] = useState(null)
  const [renameDraftValue, setRenameDraftValue] = useState('')
  const [weights, setWeights] = useState({
    ethical: 0.2,
    analytical: 0.25,
    emotional: 0.25,
    values: 0.2,
    red_team: 0.0,
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

  const { user, session, loading: authLoading, signOut } = useAuth()
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
    if (authLoading || !user || !session) return
    refreshConversations()
  }, [authLoading, user, session])

  // Removed legacy /preferences fetch to prevent old tone overrides

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

  const refreshConversations = async () => {
    setConversationsLoading(true)
    setConversationError(null)
    try {
      const data = await api.get('/conversations')
      setConversations(data || [])
    } catch (err) {
      setConversationError(err.message)
    } finally {
      setConversationsLoading(false)
    }
  }

  const hydrateHistoryMessages = (history) => {
    if (!history || !history.messages) return []
    return history.messages.map((m) => {
      if (m.role === 'user') {
        return { id: m.id, role: 'user', content: m.content }
      }

      return {
        id: m.id,
        role: 'assistant',
        data: {
          response: addFriendlyEmoji(m.content || ''),
          conversation_id: history.id,
          message_id: m.id,
          intent: null,
          complexity: null,
          thinking_trace_id: m.trace_id,
        },
        query: null,
      }
    })
  }

  const loadConversation = async (id) => {
    if (!id) return
    setLoading(true)
    setConversationError(null)
    try {
      const data = await api.get(`/conversations/${id}`)
      setConversationId(data.id)
      setMessages(hydrateHistoryMessages(data))
      setExpandedInsights({})
      setShowSidebar(false)
    } catch (err) {
      setConversationError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRenameConversation = async (conversation) => {
    if (!conversation?.id) return
    const trimmed = renameDraftValue.trim()
    if (!trimmed || trimmed === conversation.title) {
      setRenameDraftId(null)
      setRenameDraftValue('')
      return
    }

    try {
      setConversations((prev) => prev.map((c) => (
        c.id === conversation.id ? { ...c, title: trimmed, updated_at: new Date().toISOString() } : c
      )))

      await api.patch(`/conversations/${conversation.id}/title`, { title: trimmed })
      setRenameDraftId(null)
      setRenameDraftValue('')
      refreshConversations()
    } catch (err) {
      setConversationError(err.message)
      setRenameDraftId(null)
      setRenameDraftValue('')
      refreshConversations()
    }
  }

  const handleNewConversation = () => {
    setConversationId(null)
    setMessages([])
    setExpandedInsights({})
    setQuery('')
  }

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
    if (!session) {
      setError('Session not ready. Please sign in again.')
      return
    }

    const userMessage = { id: Date.now(), role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)
    setError(null)

    try {
      const payload = {
        query: text,
        brain_weights: weights,
        tone: currentTone,
      }
      // Include conversation_id for follow-up messages
      if (conversationId) {
        payload.conversation_id = conversationId
      }

      const data = await api.post('/chat', payload)

      // Track conversation for follow-ups
      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        data: { ...data, response: addFriendlyEmoji(data.response || '') },
        query: text,
      }])

      // Refresh list so sidebar shows newest title/order
      refreshConversations()
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

  const saveTone = (newTone) => {
    setCurrentTone(newTone)
  }

  const handleToneSelect = async (newTone) => {
    if (newTone === currentTone) return
    await saveTone(newTone)
  }

  const addFriendlyEmoji = (text) => {
    const emojiPool = ['🙂', '😊', '😉', '👍', '🙏', '🙌', '😅', '💡']
    const alreadyHasEmoji = /[\u{1F300}-\u{1FAFF}]/u.test(text)
    if (alreadyHasEmoji) return text
    const pick = emojiPool[text.length % emojiPool.length]
    return `${text.trim()} ${pick}`
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

      <div className="relative w-full max-w-[1200px] h-screen px-3 sm:px-6 py-3 sm:py-5 flex gap-4">
        <AnimatePresence>
          {showSidebar && (
            <motion.aside
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              transition={{ duration: 0.22 }}
              className="absolute md:static left-3 top-3 md:top-auto md:left-auto z-30 w-72 flex-none"
            >
              <div className="h-full w-full rounded-[1.75rem] border border-white/70 bg-white/90 backdrop-blur-sm shadow-[0_14px_40px_rgba(15,23,42,0.08)] flex flex-col overflow-hidden">
                <div className="px-4 py-4 border-b border-slate-200/70 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => setShowSidebar(false)}
                    className="flex items-center gap-3 text-slate-500 hover:text-slate-700"
                    aria-label="Hide conversations"
                  >
                    <span className="flex flex-col gap-[3px]" aria-hidden="true">
                      <span className="w-5 h-[2px] bg-slate-500 rounded-full" />
                      <span className="w-5 h-[2px] bg-slate-500 rounded-full" />
                      <span className="w-5 h-[2px] bg-slate-500 rounded-full" />
                    </span>
                    <div className="text-left">
                      <p className="text-[11px] uppercase tracking-[0.15em] text-slate-400">Conversations</p>
                      <p className="text-sm text-slate-600">Your recent threads</p>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={handleNewConversation}
                    className="p-2 rounded-full text-slate-500 hover:text-slate-700 hover:bg-slate-100"
                    aria-label="Start new conversation"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                  {conversationsLoading ? (
                    <div className="px-4 py-4 text-slate-400 text-sm">Loading...</div>
                  ) : conversationError ? (
                    <div className="px-4 py-4 text-red-500 text-sm">{conversationError}</div>
                  ) : conversations.length === 0 ? (
                    <div className="px-4 py-6 text-slate-400 text-sm">No conversations yet.</div>
                  ) : (
                    <ul className="divide-y divide-slate-100">
                      {conversations.map((c) => (
                        <li key={c.id}>
                          <div
                            role="button"
                            tabIndex={0}
                            onClick={() => loadConversation(c.id)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') loadConversation(c.id)
                            }}
                            className={`group flex items-center justify-between gap-2 px-4 py-3 hover:bg-slate-50 transition-colors ${
                              conversationId === c.id ? 'bg-slate-100/80' : ''
                            }`}
                          >
                            <div className="min-w-0 flex-1">
                              {renameDraftId === c.id ? (
                                <div className="flex items-center gap-2">
                                  <input
                                    autoFocus
                                    value={renameDraftValue}
                                    onChange={(e) => setRenameDraftValue(e.target.value)}
                                    onClick={(e) => e.stopPropagation()}
                                    className="flex-1 rounded-lg border border-slate-200 px-2 py-1 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-400"
                                  />
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      handleRenameConversation(c)
                                    }}
                                    className="px-2 py-1 rounded-md bg-slate-700 text-white text-xs hover:bg-slate-800"
                                  >
                                    Save
                                  </button>
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      setRenameDraftId(null)
                                      setRenameDraftValue('')
                                    }}
                                    className="px-2 py-1 rounded-md text-slate-500 hover:text-slate-700 text-xs"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : (
                                <>
                                  <p className="text-sm font-medium text-slate-700 truncate">{c.title || 'New Conversation'}</p>
                                  <p className="text-[11px] text-slate-400 mt-0.5">{c.updated_at ? new Date(c.updated_at).toLocaleString() : ''}</p>
                                </>
                              )}
                            </div>
                            {renameDraftId !== c.id && (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setRenameDraftId(c.id)
                                  setRenameDraftValue(c.title || 'New Conversation')
                                }}
                                className="p-2 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 opacity-0 group-hover:opacity-100 focus:opacity-100 transition"
                                aria-label="Rename conversation"
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {showSidebar && (
          <button
            type="button"
            className="fixed inset-0 bg-black/10 backdrop-blur-[1px] md:hidden"
            onClick={() => setShowSidebar(false)}
            aria-label="Close conversations overlay"
          />
        )}

        <div className="flex-1 h-full rounded-[2rem] sm:rounded-[2.3rem] border border-white/70 bg-white/70 backdrop-blur-sm shadow-[0_18px_50px_rgba(15,23,42,0.08)] flex flex-col overflow-hidden">
          <header className="flex-none px-4 sm:px-6 pt-4 sm:pt-5 pb-3 flex items-center justify-between border-b border-slate-200/60">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowSidebar((prev) => !prev)}
                className="p-2 -ml-2 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                aria-label="Toggle conversations"
              >
                <Menu className="w-5 h-5" />
              </button>
              <div>
                <p className="text-[11px] uppercase tracking-[0.17em] text-slate-400">MindMate</p>
                <h1 className="text-sm sm:text-base text-slate-600 mt-0.5">Calm thinking workspace</h1>
              </div>
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
                            <MarkdownRenderer content={msg.data.response} className="text-slate-800" />
                          </div>

                          {/* Intent & Complexity badges removed for a cleaner UI */}

                          {/* "See how I thought" UI completely removed */}

                          {idx === messages.length - 1 && (
                            <div className="mt-3">
                              <FeedbackPanel
                                conversationId={msg.data.conversation_id}
                                messageId={msg.data.message_id}
                                brainConfig={weights}
                              />
                            </div>
                          )}
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

              <div className="mt-2 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setShowComposerExtras((prev) => !prev)}
                  className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600 hover:border-slate-300 hover:text-slate-800 bg-white/90"
                >
                  <AlignJustify className="w-4 h-4" />
                  {showComposerExtras ? 'Hide controls' : 'Show controls'}
                </button>
                <span className="text-[11px] text-slate-400">Tone and style tweaks</span>
              </div>

              <AnimatePresence>
                {showComposerExtras && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.25 }}
                    className="overflow-hidden"
                  >
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
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </footer>
        </div>
      </div>
    </div>
  )
}
