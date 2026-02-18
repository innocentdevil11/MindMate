'use client'

import { motion } from 'framer-motion'
import MarkdownRenderer from './MarkdownRenderer'

export default function AgentCard({ name, descriptor, output, color, delay = 0 }) {
  const colorMap = {
    cyan: 'border-cyan-500/30 neon-glow-cyan',
    violet: 'border-violet-500/30 neon-glow-violet',
    emerald: 'border-emerald-500/30 neon-glow-emerald',
    pink: 'border-pink-500/30 neon-glow-pink',
    orange: 'border-orange-500/30 neon-glow-orange',
  }

  const gradientMap = {
    cyan: 'from-cyan-400 via-cyan-500 to-blue-500',
    violet: 'from-violet-400 via-purple-500 to-fuchsia-500',
    emerald: 'from-emerald-400 via-green-500 to-teal-500',
    pink: 'from-pink-400 via-rose-500 to-red-500',
    orange: 'from-orange-400 via-amber-500 to-yellow-500',
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
      initial={{ opacity: 0, y: 40, scale: 0.9, rotateX: -15 }}
      animate={{ opacity: 1, y: 0, scale: 1, rotateX: 0 }}
      whileHover={{ 
        scale: 1.03, 
        y: -8,
        transition: { duration: 0.3, ease: [0.34, 1.56, 0.64, 1] }
      }}
      transition={{ 
        duration: 0.7, 
        delay: delay,
        ease: [0.22, 1, 0.36, 1]
      }}
      className={`glass glass-hover rounded-3xl p-7 border-2 ${colorMap[color]} relative overflow-hidden group`}
      style={{
        transformStyle: 'preserve-3d',
        perspective: '1000px'
      }}
    >
      {/* Animated gradient overlay */}
      <motion.div 
        className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${gradientMap[color]}`}
        initial={{ opacity: 0.6 }}
        animate={{ opacity: [0.6, 1, 0.6] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      />
      
      {/* Animated corner accent */}
      <motion.div 
        className={`absolute bottom-0 right-0 w-24 h-24 bg-gradient-to-tl ${gradientMap[color]} opacity-10 rounded-tl-full blur-2xl`}
        animate={{ 
          scale: [1, 1.2, 1],
          opacity: [0.1, 0.15, 0.1]
        }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      />
      
      {/* Icon badge with animation */}
      <motion.div 
        className="absolute top-5 right-5 text-3xl opacity-15 group-hover:opacity-30 transition-opacity duration-300"
        animate={{ 
          rotate: [0, 5, -5, 0],
        }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      >
        {iconMap[color]}
      </motion.div>
      
      <div className="mb-5 relative z-10">
        <motion.h3 
          className={`text-2xl font-bold bg-gradient-to-r ${gradientMap[color]} bg-clip-text text-transparent inline-flex items-center gap-3 mb-2`}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: delay + 0.2 }}
        >
          <span className="text-2xl drop-shadow-lg">{iconMap[color]}</span>
          {name}
        </motion.h3>
        <motion.p 
          className="text-xs text-gray-400 font-medium tracking-wider uppercase opacity-70"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.7 }}
          transition={{ delay: delay + 0.3 }}
        >
          {descriptor}
        </motion.p>
      </div>
      
      <motion.div 
        className="text-sm leading-relaxed relative z-10"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: delay + 0.4 }}
      >
        <MarkdownRenderer content={output} />
      </motion.div>
    </motion.div>
  )
}
