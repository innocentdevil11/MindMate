'use client'

import { motion } from 'framer-motion'

export default function WeightSlider({ 
  label, 
  value, 
  onChange, 
  color = 'cyan',
  disabled = false 
}) {
  const activeColors = {
    cyan: '#0ea5e9', // sky-500
    violet: '#8b5cf6', // violet-500
    emerald: '#10b981', // emerald-500
    pink: '#ec4899', // pink-500
    orange: '#f97316', // orange-500
  }

  const activeColor = activeColors[color] || '#cbd5e1'
  const percentage = value * 100

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3 group"
    >
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-slate-600 transition-colors duration-300">
          {label}
        </label>
        <span
          className="text-xs font-bold px-2 py-1 rounded-md bg-slate-50 border border-slate-100"
          style={{ color: activeColor }}
        >
          {(value * 10).toFixed(1)} / 10
        </span>
      </div>
      
      <div className="relative h-2">
        {/* Track background */}
        <div className="absolute inset-0 rounded-full bg-slate-100 overflow-hidden border border-slate-200 shadow-inner">
          {/* Filled track */}
          <motion.div 
            className="h-full rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            style={{ background: activeColor }}
          />
        </div>
        
        {/* Custom thumb */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-white shadow-md cursor-pointer pointer-events-none z-10"
          style={{
            left: `calc(${percentage}% - 8px)`,
            border: `2px solid ${activeColor}`,
          }}
          whileHover={{ scale: 1.1 }}
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
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed z-20"
        />
      </div>
    </motion.div>
  )
}
