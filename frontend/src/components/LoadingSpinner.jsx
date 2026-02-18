'use client'

import { motion } from 'framer-motion'

export default function LoadingSpinner() {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className="flex flex-col items-center justify-center py-20"
    >
      <div className="relative w-32 h-32">
        {/* Outer rotating ring with gradient */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 rounded-full"
          style={{
            background: 'conic-gradient(from 0deg, transparent 0%, #06fff0 50%, transparent 100%)',
            filter: 'blur(8px)'
          }}
        />
        
        {/* Middle counter-rotating ring */}
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-2 rounded-full"
          style={{
            background: 'conic-gradient(from 0deg, transparent 0%, #a855f7 50%, transparent 100%)',
            filter: 'blur(6px)'
          }}
        />
        
        {/* Solid border rings */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 border-4 border-transparent border-t-cyan-500 rounded-full"
        />
        
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-3 border-4 border-transparent border-t-violet-500 rounded-full"
        />
        
        {/* Inner pulsing circle */}
        <motion.div
          animate={{ 
            scale: [1, 1.3, 1], 
            opacity: [0.6, 1, 0.6] 
          }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute inset-0 m-auto w-12 h-12 bg-gradient-to-br from-cyan-500/40 to-violet-500/40 rounded-full blur-md"
        />
        
        {/* Center dot */}
        <motion.div
          animate={{ 
            boxShadow: [
              '0 0 20px rgba(6, 255, 240, 0.8)',
              '0 0 40px rgba(168, 85, 247, 0.8)',
              '0 0 20px rgba(6, 255, 240, 0.8)'
            ]
          }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute inset-0 m-auto w-3 h-3 bg-white rounded-full"
        />
      </div>
      
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mt-10 text-center"
      >
        <motion.p
          animate={{ opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="text-lg font-semibold bg-gradient-to-r from-cyan-400 via-violet-400 to-emerald-400 bg-clip-text text-transparent"
        >
          Council Deliberating...
        </motion.p>
        <motion.p
          animate={{ opacity: [0.4, 0.7, 0.4] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
          className="mt-2 text-sm text-gray-500 font-medium"
        >
          Analyzing perspectives
        </motion.p>
      </motion.div>
    </motion.div>
  )
}
