'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function AudioRecorder({ onTranscription, onDecision, weights, isLoading }) {
  const [isRecording, setIsRecording] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState(null)
  const [recordingTime, setRecordingTime] = useState(0)

  const mediaRecorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)
  const wsRef = useRef(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }
  }, [])

  const startRecording = async () => {
    try {
      setError(null)
      setTranscript('')
      chunksRef.current = []
      setRecordingTime(0)

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      })

      streamRef.current = stream
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorder.start(100)
      setIsRecording(true)

      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

    } catch (err) {
      setError(err.message || 'Failed to access microphone')
    }
  }

  const stopRecording = async () => {
    return new Promise((resolve) => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.onstop = () => {
          setIsRecording(false)
          if (timerRef.current) clearInterval(timerRef.current)
          resolve()
        }
        mediaRecorderRef.current.stop()
      } else {
        resolve()
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    })
  }

  const sendAudioToTranscribe = async (useWebSocket = true) => {
    if (chunksRef.current.length === 0) {
      setError('No audio recorded')
      return
    }

    setIsSending(true)
    setError(null)

    try {
      const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })

      if (useWebSocket) {
        await transcribeViaWebSocket(audioBlob)
      } else {
        await transcribeViaRest(audioBlob)
      }
    } catch (err) {
      setError(err.message || 'Transcription failed')
    } finally {
      setIsSending(false)
    }
  }

  const transcribeViaWebSocket = (audioBlob) => {
    return new Promise((resolve, reject) => {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const wsUrl = API_URL.replace('http', 'ws') + '/ws/transcribe-live'

      console.log('[AudioRecorder] Connecting to WebSocket:', wsUrl)
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws
      let timeoutId

      ws.onopen = async () => {
        console.log('[AudioRecorder] WebSocket connected')
        try {
          const reader = new FileReader()
          reader.onload = async () => {
            const base64Audio = reader.result.split(',')[1]
            console.log('[AudioRecorder] Sending audio:', base64Audio.length, 'bytes')

            ws.send(JSON.stringify({
              type: 'audio',
              data: base64Audio,
              language: 'en'
            }))

            // Increased timeout for Whisper model to initialize (up to 2 seconds)
            setTimeout(() => {
              console.log('[AudioRecorder] Sending transcribe request')
              ws.send(JSON.stringify({ type: 'transcribe' }))
            }, 2000)
          }
          reader.readAsDataURL(audioBlob)

          timeoutId = setTimeout(() => {
            console.error('[AudioRecorder] Transcription timeout - no response after 30 seconds')
            ws.close()
            reject(new Error('Transcription timeout'))
          }, 30000)
        } catch (err) {
          console.error('[AudioRecorder] Error in onopen:', err)
          reject(err)
        }
      }

      ws.onmessage = (event) => {
        console.log('[AudioRecorder] Received message:', event.data)
        try {
          const message = JSON.parse(event.data)

          if (message.type === 'transcription') {
            console.log('[AudioRecorder] Transcription received:', message.text)
            clearTimeout(timeoutId)
            setTranscript(message.text)
            onTranscription(message.text)
            ws.close()
            resolve()
          } else if (message.type === 'error') {
            console.error('[AudioRecorder] Server error:', message.message)
            clearTimeout(timeoutId)
            reject(new Error(message.message))
          } else if (message.type === 'ack') {
            console.log('[AudioRecorder] Audio acknowledged:', message)
          }
        } catch (err) {
          console.error('[AudioRecorder] Error parsing message:', err)
          reject(err)
        }
      }

      ws.onerror = (error) => {
        console.error('[AudioRecorder] WebSocket error:', error)
        clearTimeout(timeoutId)
        reject(error)
      }

      ws.onclose = () => {
        console.log('[AudioRecorder] WebSocket closed')
        clearTimeout(timeoutId)
      }
    })
  }

  const transcribeViaRest = async (audioBlob) => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

    const formData = new FormData()
    formData.append('file', audioBlob, 'audio.webm')

    const response = await fetch(`${API_URL}/transcribe`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Transcription failed')
    }

    const data = await response.json()
    setTranscript(data.text)
    onTranscription(data.text)
  }

  const handleTranscribeAndDecide = async () => {
    if (chunksRef.current.length === 0) {
      setError('No audio recorded')
      return
    }

    setIsSending(true)
    setError(null)

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const wsUrl = API_URL.replace('http', 'ws') + '/ws/transcribe-and-decide'

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = async () => {
        try {
          ws.send(JSON.stringify({
            type: 'weights',
            weights: weights
          }))

          const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
          const reader = new FileReader()

          reader.onload = () => {
            const base64Audio = reader.result.split(',')[1]
            ws.send(JSON.stringify({
              type: 'audio',
              data: base64Audio,
              language: 'en'
            }))

            setTimeout(() => {
              ws.send(JSON.stringify({ type: 'DECIDE' }))
            }, 500)
          }

          reader.readAsDataURL(audioBlob)
        } catch (err) {
          setError(err.message)
        }
      }

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data)

        if (message.type === 'transcribed') {
          setTranscript(message.text)
          onTranscription(message.text)
        } else if (message.type === 'agent_response') {
          onDecision(message)
        } else if (message.type === 'final_decision') {
          setIsSending(false)
          onDecision(message)
          ws.close()
        } else if (message.type === 'error') {
          setError(message.message)
          setIsSending(false)
          ws.close()
        }
      }

      ws.onerror = (error) => {
        setError('WebSocket error')
        setIsSending(false)
      }
    } catch (err) {
      setError(err.message)
      setIsSending(false)
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl mx-auto mb-8"
    >
      <div className="relative group">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 via-violet-500 to-emerald-500 rounded-2xl blur opacity-0 group-hover:opacity-50 transition duration-500" />

        <div className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-8 border border-slate-700">
          <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-violet-400 mb-6">
            🎤 Live Audio Input
          </h3>

          <AnimatePresence>
            {isRecording && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.8, repeat: Infinity }}
                    className="w-3 h-3 bg-red-500 rounded-full"
                  />
                  <span className="text-red-400 font-semibold">Recording...</span>
                </div>
                <span className="text-red-300 font-mono">{formatTime(recordingTime)}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {transcript && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-slate-700/50 rounded-lg border border-cyan-500/30"
            >
              <p className="text-sm text-gray-400 mb-2">Transcribed:</p>
              <p className="text-white leading-relaxed">{transcript}</p>
            </motion.div>
          )}

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg"
              >
                <p className="text-red-400 text-sm">{error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex gap-3 flex-wrap">
            {!isRecording ? (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={startRecording}
                disabled={isSending}
                suppressHydrationWarning
                className="flex-1 min-w-[150px] px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-semibold rounded-lg disabled:opacity-50 transition"
              >
                🔴 Start Recording
              </motion.button>
            ) : (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={stopRecording}
                suppressHydrationWarning
                className="flex-1 min-w-[150px] px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold rounded-lg transition"
              >
                ⏹️ Stop Recording
              </motion.button>
            )}

            {!isRecording && chunksRef.current.length > 0 && (
              <>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => sendAudioToTranscribe(true)}
                  disabled={isSending || isLoading}
                  className="flex-1 min-w-[150px] px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white font-semibold rounded-lg disabled:opacity-50 transition"
                >
                  {isSending ? '⏳ Transcribing...' : '✨ Transcribe'}
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleTranscribeAndDecide}
                  disabled={isSending || isLoading}
                  className="flex-1 min-w-[150px] px-6 py-3 bg-gradient-to-r from-violet-500 to-violet-600 hover:from-violet-600 hover:to-violet-700 text-white font-semibold rounded-lg disabled:opacity-50 transition"
                >
                  {isSending ? '⏳ Deciding...' : '🧠 Transcribe & Decide'}
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    setTranscript('')
                    chunksRef.current = []
                    setRecordingTime(0)
                  }}
                  className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition"
                >
                  🗑️ Clear
                </motion.button>
              </>
            )}
          </div>

          <p className="text-xs text-gray-500 mt-4">
            💡 Tip: Use headphones to avoid echo. Audio processing runs locally with zero latency!
          </p>
        </div>
      </div>
    </motion.div>
  )
}
