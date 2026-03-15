'use client'

/**
 * ThinkingTracePanel — MindMate v3
 *
 * Fetches and displays the AI's internal reasoning pipeline.
 * Shows intent classification, complexity routing, agent reasoning,
 * debate critiques, and conflict resolution steps.
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Brain, Zap, MessageSquare, Scale, Lightbulb, Sparkles } from 'lucide-react'
import { api } from '@/lib/api'

const STEP_CONFIG = {
  intent: { icon: Zap, label: 'Intent', color: 'text-indigo-500 bg-indigo-50 border-indigo-100' },
  complexity: { icon: Brain, label: 'Complexity', color: 'text-amber-600 bg-amber-50 border-amber-100' },
  agent_reasoning: { icon: MessageSquare, label: 'Agent', color: 'text-violet-500 bg-violet-50 border-violet-100' },
  debate_critique: { icon: Scale, label: 'Debate', color: 'text-orange-500 bg-orange-50 border-orange-100' },
  conflict_resolution: { icon: Lightbulb, label: 'Resolution', color: 'text-blue-500 bg-blue-50 border-blue-100' },
  personality_styling: { icon: Sparkles, label: 'Style', color: 'text-pink-500 bg-pink-50 border-pink-100' },
  response_control: { icon: Zap, label: 'Control', color: 'text-emerald-500 bg-emerald-50 border-emerald-100' },
  memory_retrieval: { icon: Brain, label: 'Memory', color: 'text-cyan-500 bg-cyan-50 border-cyan-100' },
  final_output: { icon: Sparkles, label: 'Output', color: 'text-slate-600 bg-slate-50 border-slate-200' },
}

export default function ThinkingTracePanel({ conversationId, messageId }) {
  const [steps, setSteps] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!conversationId) return

    const fetchTrace = async () => {
      try {
        setLoading(true)
        const url = messageId
          ? `/trace/${conversationId}?message_id=${messageId}`
          : `/trace/${conversationId}`

        const data = await api.get(url)
        setSteps(data.steps || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchTrace()
  }, [conversationId, messageId])

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-4 text-slate-400">
        <div className="w-4 h-4 border-2 border-slate-300 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs">Loading thinking trace...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-xs text-red-400 py-2">
        Could not load thinking trace.
      </div>
    )
  }

  if (steps.length === 0) {
    return (
      <div className="text-xs text-slate-400 py-2 italic">
        No thinking trace available.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1">
      <p className="text-[10px] uppercase tracking-[0.15em] text-slate-400 mb-1.5">
        How I Thought
      </p>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-[15px] top-3 bottom-3 w-px bg-slate-200" />

        {steps.map((step, idx) => {
          const config = STEP_CONFIG[step.step_type] || STEP_CONFIG.final_output
          const Icon = config.icon

          return (
            <motion.div
              key={step.id || idx}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2, delay: idx * 0.04 }}
              className="relative flex items-start gap-3 py-1.5"
            >
              {/* Timeline dot */}
              <div className={`relative z-10 w-[30px] h-[30px] rounded-full flex items-center justify-center border ${config.color} shrink-0`}>
                <Icon className="w-3.5 h-3.5" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 pt-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-medium text-slate-600">
                    {config.label}
                  </span>
                  {step.agent && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                      {step.agent}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                  {step.content}
                </p>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
