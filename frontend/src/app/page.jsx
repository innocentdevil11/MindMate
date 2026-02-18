'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import WeightSlider from '@/components/WeightSlider'
import AgentCard from '@/components/AgentCard'
import LoadingSpinner from '@/components/LoadingSpinner'
import MarkdownRenderer from '@/components/MarkdownRenderer.jsx'
import AudioRecorder from '@/components/AudioRecorder'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const agentConfig = [
  { key: 'ethical', label: 'Ethical', descriptor: 'Moral & philosophical perspective', color: 'violet' },
  { key: 'risk', label: 'Risk & Logic', descriptor: 'Analytical risk assessment', color: 'orange' },
  { key: 'eq', label: 'EQ', descriptor: 'Emotional intelligence lens', color: 'pink' },
  { key: 'values', label: 'Value Alignment', descriptor: 'Personal values harmony', color: 'emerald' },
  { key: 'red_team', label: 'Red Team', descriptor: 'Devil\'s advocate perspective', color: 'cyan' },
]

export default function Home() {
  const [query, setQuery] = useState('')
  const [weights, setWeights] = useState({
    ethical: 0.2,
    risk: 0.2,
    eq: 0.2,
    values: 0.2,
    red_team: 0.2,
  })
  
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [streamingResults, setStreamingResults] = useState(null)

  const handleSubmit = async () => {
    if (!query.trim()) return
    
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          weights,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to get decision')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const updateWeight = (key, value) => {
    setWeights(prev => ({ ...prev, [key]: value }))
  }

  const handleTranscription = (transcribedText) => {
    setQuery(transcribedText)
  }

  const handleDecisionFromAudio = (message) => {
    if (message.type === 'agent_response') {
      // Stream agent responses in real-time
      setStreamingResults(prev => ({
        ...prev,
        [message.agent]: message.output
      }))
    } else if (message.type === 'final_decision') {
      // Consolidate all results
      const agentOutputs = {}
      agentConfig.forEach(agent => {
        agentOutputs[agent.key] = streamingResults?.[agent.key] || ''
      })
      setResult({
        agent_outputs: agentOutputs,
        final_decision: message.decision
      })
      setStreamingResults(null)
    }
  }

  return (
    <div className="min-h-screen gradient-bg">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -40, scale: 0.85 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-20 relative"
        >
          {/* Decorative glow effect */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[200px] bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-emerald-500/10 blur-3xl -z-10" />
          
          <motion.div
            animate={{ 
              textShadow: [
                '0 0 30px rgba(6, 255, 240, 0.4)',
                '0 0 50px rgba(168, 85, 247, 0.5)',
                '0 0 30px rgba(16, 185, 129, 0.4)',
                '0 0 30px rgba(6, 255, 240, 0.4)'
              ]
            }}
            transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <h1 className="text-8xl font-black mb-6 bg-gradient-to-r from-cyan-400 via-violet-500 to-emerald-400 bg-clip-text text-transparent leading-tight tracking-tight">
              <motion.span
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="inline-block"
              >
                ✨
              </motion.span>
              {' '}
              <motion.span
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="inline-block"
              >
                Mind
              </motion.span>
              <motion.span
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="inline-block"
              >
                Mate
              </motion.span>
            </h1>
          </motion.div>
          <motion.p 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="text-gray-300 text-xl font-light tracking-wide mb-2"
          >
            A private board of <span className="text-cyan-400 font-bold">AI directors</span> helping you think clearly
          </motion.p>
          
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="text-gray-500 text-sm font-medium"
          >
            Make better decisions with multi-perspective AI analysis
          </motion.p>
          
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1, type: 'spring', stiffness: 200, damping: 15 }}
            className="mt-8 inline-flex items-center gap-2 px-6 py-3 glass rounded-full text-sm text-gray-300 border border-emerald-500/30 neon-glow-emerald"
          >
            <motion.span 
              animate={{ scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              className="inline-block w-2 h-2 bg-emerald-400 rounded-full shadow-lg shadow-emerald-500/50"
            />
            <span className="font-semibold">Multi-Agent Decision Intelligence</span>
          </motion.div>
        </motion.div>

        {/* Query Input */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="mb-12"
        >
          <div className="glass rounded-3xl p-10 border-2 border-violet-500/30 relative overflow-hidden group hover:border-violet-500/50 transition-all duration-500">
            {/* Animated background glow */}
            <motion.div 
              className="absolute inset-0 bg-gradient-to-br from-violet-500/5 via-transparent to-cyan-500/5"
              animate={{ 
                opacity: [0.3, 0.5, 0.3],
              }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            />
            
            {/* Decorative corner accents */}
            <motion.div 
              className="absolute top-0 left-0 w-32 h-32 bg-gradient-to-br from-violet-500/20 to-transparent rounded-br-full blur-2xl"
              animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
            />
            <motion.div 
              className="absolute bottom-0 right-0 w-32 h-32 bg-gradient-to-tl from-cyan-500/20 to-transparent rounded-tl-full blur-2xl"
              animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut', delay: 2.5 }}
            />
            
            <label className="relative z-10 block text-base font-bold text-gray-100 mb-5 tracking-wide uppercase flex items-center gap-3 group-hover:text-cyan-300 transition-colors duration-300">
              <span className="text-2xl">💭</span> 
              <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">Your Dilemma</span>
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
              placeholder="Should I leave my current job to start a startup? What factors should I consider?"
              className="relative z-10 w-full h-48 bg-black/40 border-2 border-gray-700/50 rounded-2xl px-6 py-5 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 focus:bg-black/50 resize-none transition-all duration-300 disabled:opacity-50 font-light text-lg leading-relaxed backdrop-blur-sm"
            />
            
            {/* Audio Input Section */}
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              transition={{ delay: 0.2 }}
              className="mt-8 pt-8 border-t border-gray-700/30"
            >
              <AudioRecorder 
                onTranscription={handleTranscription}
                onDecision={handleDecisionFromAudio}
                weights={weights}
                isLoading={loading}
              />
            </motion.div>
          </div>
        </motion.div>

        {/* Weight Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="glass rounded-3xl p-8 mb-10 border border-gray-700/50"
        >
          <h2 className="text-2xl font-bold text-gray-100 mb-8 flex items-center gap-3">
            <span className="text-3xl">⚡</span>
            <span className="bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
              Agent Influence
            </span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {agentConfig.map((agent, idx) => (
              <motion.div
                key={agent.key}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + idx * 0.1 }}
              >
                <WeightSlider
                  label={agent.label}
                  value={weights[agent.key]}
                  onChange={(val) => updateWeight(agent.key, val)}
                  color={agent.color}
                  disabled={loading}
                />
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Submit Button */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.8, type: 'spring', stiffness: 200, damping: 15 }}
          className="flex justify-center mb-20"
        >
          <motion.button
            onClick={handleSubmit}
            disabled={loading || !query.trim()}
            whileHover={{ 
              scale: loading ? 1 : 1.05,
              boxShadow: loading ? undefined : '0 0 60px rgba(6, 255, 240, 0.6), 0 0 100px rgba(168, 85, 247, 0.4)'
            }}
            whileTap={{ scale: loading ? 1 : 0.95 }}
            className="group relative px-16 py-6 bg-gradient-to-r from-cyan-500 via-violet-500 to-emerald-500 rounded-2xl font-bold text-white text-xl shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all overflow-hidden"
            style={{
              boxShadow: '0 0 40px rgba(6, 255, 240, 0.4), 0 0 80px rgba(168, 85, 247, 0.3)'
            }}
          >
            {/* Animated background shine */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/25 to-transparent"
              animate={{
                x: loading ? ['-200%', '200%'] : 0
              }}
              transition={{
                duration: 1.2,
                repeat: loading ? Infinity : 0,
                ease: 'linear'
              }}
            />
            
            {/* Particle effects on hover */}
            {!loading && (
              <motion.div
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              >
                {[...Array(3)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="absolute w-1 h-1 bg-white rounded-full"
                    animate={{
                      x: [Math.random() * 100 - 50, Math.random() * 100 - 50],
                      y: [Math.random() * 100 - 50, Math.random() * 100 - 50],
                      opacity: [0, 1, 0]
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      delay: i * 0.3
                    }}
                    style={{ left: '50%', top: '50%' }}
                  />
                ))}
              </motion.div>
            )}
            
            <span className="relative z-10 flex items-center gap-4">
              {loading ? (
                <>
                  <motion.span
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="text-2xl"
                  >
                    ⚙️
                  </motion.span>
                  <span className="tracking-wide">Processing...</span>
                </>
              ) : (
                <>
                  <span className="text-2xl">🚀</span>
                  <span className="tracking-wide">Run MindMate</span>
                </>
              )}
            </span>
          </motion.button>
        </motion.div>

        {/* Error Display */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="glass rounded-xl p-4 mb-8 border-red-500/30 bg-red-500/10"
            >
              <p className="text-red-400 text-sm">
                <strong>Error:</strong> {error}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Loading State */}
        <AnimatePresence>
          {loading && <LoadingSpinner />}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {result && !loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-8"
            >
              {/* Final Decision - Prominent */}
              <motion.div
                initial={{ opacity: 0, y: 40, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                className="glass rounded-3xl p-10 border-3 border-emerald-500/40 neon-glow-emerald relative overflow-hidden"
              >
                {/* Decorative elements */}
                <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-emerald-500 via-cyan-500 to-violet-500 opacity-60" />
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-emerald-500/10 rounded-full blur-3xl" />
                <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-cyan-500/10 rounded-full blur-3xl" />
                
                <div className="relative z-10">
                  <motion.h2 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-4xl font-bold mb-6 bg-gradient-to-r from-emerald-400 via-green-500 to-teal-400 bg-clip-text text-transparent flex items-center gap-3"
                  >
                    <span className="text-4xl">🎯</span>
                    Council Resolution
                  </motion.h2>
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="text-lg leading-relaxed"
                  >
                    <MarkdownRenderer content={result.final_decision} />
                  </motion.div>
                </div>
              </motion.div>

              {/* Agent Outputs */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
              >
                <motion.h2 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-3xl font-bold text-gray-100 mb-8 flex items-center gap-3"
                >
                  <span className="text-3xl">🧠</span>
                  <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
                    Individual Perspectives
                  </span>
                </motion.h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {agentConfig.map((agent, idx) => (
                    <AgentCard
                      key={agent.key}
                      name={agent.label}
                      descriptor={agent.descriptor}
                      output={result.agent_outputs[agent.key]}
                      color={agent.color}
                      delay={0.8 + idx * 0.15}
                    />
                  ))}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
