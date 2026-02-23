'use client'

import { motion } from 'framer-motion'
import MarkdownRenderer from './MarkdownRenderer'

export default function AgentCard({ name, descriptor, output, color, delay = 0 }) {
  const colorMap = {
    cyan: 'bg-cyan-50/60 text-cyan-900 border-cyan-100/50',
    violet: 'bg-violet-50/60 text-violet-900 border-violet-100/50',
    emerald: 'bg-emerald-50/60 text-emerald-900 border-emerald-100/50',
    pink: 'bg-pink-50/60 text-pink-900 border-pink-100/50',
    orange: 'bg-orange-50/60 text-orange-900 border-orange-100/50',
  }

  const iconMap = {
    cyan: '🔴', // Red Team
    violet: '⚖️', // Ethical
    emerald: '💚', // Values
    pink: '❤️', // EQ
    orange: '⚠️', // Risk
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.8, delay: delay, ease: [0.22, 1, 0.36, 1] }}
      className={`rounded-[2rem] p-6 border ${colorMap[color]} backdrop-blur-sm`}
    >
      <div className="flex items-center gap-3 mb-3 border-b border-black/5 pb-3">
        <span className="text-xl">{iconMap[color] || '🤖'}</span>
        <div>
          <h3 className="font-semibold text-slate-700 text-[15px] tracking-tight">
            {name}
          </h3>
          <p className="text-xs text-slate-500 font-medium">{descriptor}</p>
        </div>
      </div>

      <div className="text-sm font-light leading-relaxed text-slate-600 prose prose-sm prose-slate max-w-none">
        {output ? (
          <MarkdownRenderer content={output} />
        ) : (
          <span className="italic opacity-50">No output</span>
        )}
      </div>
    </motion.div>
  )
}
