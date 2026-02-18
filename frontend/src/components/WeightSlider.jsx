'use client'

import { motion } from 'framer-motion'

export default function WeightSlider({ 
  label, 
  value, 
  onChange, 
  color = 'cyan',
  disabled = false 
}) {
  // Active color values for gradient
  const activeColors = {
    cyan: '#06fff0',
    violet: '#a855f7',
    emerald: '#10b981',
    pink: '#f754d4',
    orange: '#ff8c42',
  }

  const glowColors = {
    cyan: 'rgba(6, 255, 240, 0.5)',
    violet: 'rgba(168, 85, 247, 0.5)',
    emerald: 'rgba(16, 185, 129, 0.5)',
    pink: 'rgba(247, 84, 212, 0.5)',
    orange: 'rgba(255, 140, 66, 0.5)',
  }

  const activeColor = activeColors[color]
  const glowColor = glowColors[color]
  const percentage = value * 100

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4 group"
    >
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-gray-300 group-hover:text-gray-100 transition-colors duration-300">
          {label}
        </label>
        <motion.span
          key={value}
          initial={{ scale: 1.3, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          className="text-base font-bold px-3 py-1 rounded-lg"
          style={{
            color: activeColor,
            background: 'rgba(255,255,255,0.05)',
            border: `1px solid ${activeColor}30`,
            textShadow: `0 0 10px ${glowColor}`
          }}
        >
          {value.toFixed(2)}
        </motion.span>
      </div>
      
      <div className="relative h-3">
        {/* Track background */}
        <div 
          className="absolute inset-0 rounded-full overflow-hidden"
          style={{
            background: 'rgba(31, 41, 55, 0.8)',
            border: '1px solid rgba(255,255,255,0.1)'
          }}
        >
          {/* Filled track */}
          <motion.div 
            className="h-full rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            style={{
              background: `linear-gradient(90deg, ${activeColor}dd, ${activeColor})`,
              boxShadow: `0 0 15px ${glowColor}, 0 0 30px ${glowColor}`
            }}
          />
        </div>
        
        {/* Custom thumb */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full cursor-pointer z-10"
          style={{
            left: `calc(${percentage}% - 10px)`,
            background: `linear-gradient(135deg, white, ${activeColor}50)`,
            border: `2px solid ${activeColor}`,
            boxShadow: `0 0 15px ${glowColor}, 0 2px 8px rgba(0,0,0,0.3)`
          }}
          whileHover={{ scale: 1.2 }}
          whileTap={{ scale: 0.95 }}
        />
        
        {/* Invisible range input for interaction */}
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          disabled={disabled}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
          style={{ margin: 0 }}
        />
      </div>
    </motion.div>
  )
}
