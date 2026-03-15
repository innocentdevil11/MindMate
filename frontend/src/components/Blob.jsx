import { memo, useEffect, useState } from 'react'
import { motion } from 'framer-motion'

const sizeMap = {
  xs: 'w-7 h-7 sm:w-8 sm:h-8',
  sm: 'w-28 h-28 sm:w-32 sm:h-32',
  md: 'w-40 h-40 sm:w-44 sm:h-44',
  lg: 'w-56 h-56 sm:w-64 sm:h-64',
}

const toneGradient = {
  clean: 'from-[#e8f8fb] via-[#e3f4f2] to-[#dbe8f9]',
  casual: 'from-[#e4f5ff] via-[#dff5ed] to-[#d8e9ff]',
  blunt: 'from-[#e8eef8] via-[#e0edf4] to-[#dce6f2]',
  blunt_profane: 'from-[#e8f5ff] via-[#dff0ef] to-[#eadffd]',
}

const LOADING_FACES = ['casual', 'clean', 'blunt', 'blunt_profane']

const EyeShine = () => (
  <>
    <div className="absolute top-[2px] left-[2px] w-1.5 h-1.5 rounded-full bg-white/90" />
    <div className="absolute bottom-[3px] right-[3px] w-1 h-1 rounded-full bg-white/80" />
  </>
)

function Eyes({ tone }) {
  if (tone === 'clean') {
    return (
      <div className="absolute inset-0 flex items-center justify-center gap-6 pb-3">
        {[0, 1].map((i) => (
          <div key={i} className="w-5 h-5 rounded-full bg-slate-700 relative shadow-[0_2px_6px_rgba(0,0,0,0.15)]">
            <EyeShine />
          </div>
        ))}
      </div>
    )
  }

  if (tone === 'casual') {
    return (
      <div className="absolute inset-0 flex items-center justify-center gap-6 pb-3">
        {[0, 1].map((i) => (
          <div key={i} className="relative w-5 h-5 rounded-full bg-slate-700 shadow-[0_2px_6px_rgba(0,0,0,0.15)]">
            <EyeShine />
            <div className={`absolute -top-2 left-0 right-0 mx-auto h-1 rounded-full bg-slate-600/80 ${i === 1 ? 'rotate-6' : '-rotate-4'}`} />
          </div>
        ))}
      </div>
    )
  }

  if (tone === 'blunt') {
    return (
      <div className="absolute inset-0 flex items-center justify-center gap-5 pb-2">
        {[0, 1].map((i) => (
          <div key={i} className="relative flex items-center justify-center">
            <div className="absolute -top-1 left-0 right-0 h-1.5 bg-slate-900 rounded-full" />
            <div className="w-6 h-3 rounded-[6px] bg-slate-900" />
          </div>
        ))}
      </div>
    )
  }

  if (tone === 'blunt_profane') {
    return (
      <div className="absolute inset-0 flex items-center justify-center gap-7 pb-2">
        <div className="relative flex items-center gap-1">
          <div className="w-5 h-3 rounded-full bg-slate-800 relative">
            <EyeShine />
          </div>
          <div className="absolute -top-2 left-0 right-0 h-1 bg-slate-800 rounded-full rotate-3" />
        </div>
        <div className="relative w-5 h-5">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-4 h-1 rounded-full bg-slate-800 rotate-12" />
          </div>
          <div className="absolute -top-2 right-0 w-4 h-1 bg-slate-800 rounded-full -rotate-6" />
        </div>
      </div>
    )
  }

  return (
    <div className="absolute inset-0 flex items-center justify-center gap-6 pb-3">
      <div className="w-4.5 h-4.5 rounded-full bg-slate-700 relative">
        <EyeShine />
      </div>
      <div className="w-4.5 h-4.5 rounded-full bg-slate-700 relative">
        <EyeShine />
      </div>
    </div>
  )
}

function Mouth({ tone }) {
  if (tone === 'blunt') {
    return <div className="w-12 h-[3px] rounded-full bg-slate-900" />
  }

  if (tone === 'blunt_profane') {
    return (
      <div className="px-3 py-1 rounded-lg bg-slate-900 text-white text-[10px] font-semibold tracking-[0.08em] shadow-sm">
        #@!*
      </div>
    )
  }

  if (tone === 'casual') {
    return (
      <div className="relative w-12 h-6">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-10 h-4 border-b-[3px] border-slate-700 rounded-full" />
        </div>
      </div>
    )
  }

  // clean and default
  return <div className="w-10 h-4 border-b-[3px] border-slate-700 rounded-full" />
}

function BlobBase({ isListening = false, isThinking = false, tone = 'clean', size = 'lg' }) {
  const [loadingFaceIndex, setLoadingFaceIndex] = useState(0)

  useEffect(() => {
    if (!isThinking) return

    const interval = setInterval(() => {
      setLoadingFaceIndex((prev) => (prev + 1) % LOADING_FACES.length)
    }, 2200)

    return () => clearInterval(interval)
  }, [isThinking])

  const effectiveTone = isThinking ? LOADING_FACES[loadingFaceIndex] : tone
  const small = size === 'xs'
  const motionMode = isListening ? 'listen' : isThinking ? 'think' : 'idle'

  const haloAnimate =
    motionMode === 'listen'
      ? { opacity: [0.5, 0.8, 0.5], scale: [1, 1.1, 1] }
      : motionMode === 'think'
        ? { y: [0, -3, 0], opacity: [0.45, 0.72, 0.45], scale: [1, 1.08, 1] }
        : { y: [0, -2, 0], opacity: [0.35, 0.56, 0.35], scale: [1, 1.06, 1] }

  const haloTransition =
    motionMode === 'listen'
      ? { duration: 1.1, repeat: Infinity, ease: 'easeInOut' }
      : motionMode === 'think'
        ? { duration: 2.3, repeat: Infinity, ease: 'easeInOut' }
        : { duration: 2.3, repeat: Infinity, ease: 'easeInOut' }

  const blobAnimate =
    motionMode === 'listen'
      ? {
          borderRadius: [
            '43% 57% 54% 46% / 45% 50% 50% 55%',
            '48% 52% 50% 50% / 50% 46% 54% 50%',
            '43% 57% 54% 46% / 45% 50% 50% 55%',
          ],
          y: [0, -2, 0],
          scale: [1, 1.04, 1],
        }
      : motionMode === 'think'
        ? {
            borderRadius: [
              '50% 50% 48% 52% / 52% 48% 52% 48%',
              '48% 52% 50% 50% / 49% 51% 47% 53%',
              '50% 50% 48% 52% / 52% 48% 52% 48%',
            ],
            y: [0, -3, 0],
            scale: [1, 1.03, 1],
          }
        : {
            borderRadius: [
              '50% 50% 48% 52% / 52% 48% 52% 48%',
              '47% 53% 50% 50% / 49% 51% 46% 54%',
              '50% 50% 48% 52% / 52% 48% 52% 48%',
            ],
            y: [0, -2, 0],
            scale: [1, 1.025, 1],
          }

  const blobTransition =
    motionMode === 'listen'
      ? { duration: 1.1, repeat: Infinity, ease: 'easeInOut' }
      : motionMode === 'think'
        ? { duration: 2.5, repeat: Infinity, ease: 'easeInOut' }
        : { duration: 2.5, repeat: Infinity, ease: 'easeInOut' }

  const faceAnimate =
    motionMode === 'listen'
      ? { y: [0, -1.5, 0], scale: [1, 1.02, 1] }
      : motionMode === 'think'
        ? { y: [0, -2, 0], scale: [1, 1.02, 1] }
        : { y: [0, -1, 0], scale: [1, 1.01, 1] }

  const faceTransition =
    motionMode === 'listen'
      ? { duration: 1.1, repeat: Infinity, ease: 'easeInOut' }
      : motionMode === 'think'
        ? { duration: 2.5, repeat: Infinity, ease: 'easeInOut' }
        : { duration: 2.5, repeat: Infinity, ease: 'easeInOut' }

  return (
    <div className={`relative ${sizeMap[size] || sizeMap.lg} flex items-center justify-center transform-gpu`}>
      <motion.div
        className={`absolute inset-0 rounded-full bg-sky-100/45 ${small ? 'blur-sm' : 'blur-2xl'}`}
        animate={haloAnimate}
        transition={haloTransition}
      />

      <motion.div
        className={`relative w-full h-full overflow-hidden bg-gradient-to-br ${toneGradient[effectiveTone] || toneGradient.clean} ${small ? 'shadow-[inset_0_-8px_16px_rgba(15,23,42,0.06),0_6px_14px_rgba(148,163,184,0.20)]' : 'shadow-[inset_0_-24px_60px_rgba(15,23,42,0.08),0_18px_36px_rgba(148,163,184,0.24)]'}`}
        animate={blobAnimate}
        transition={blobTransition}
      >
        <motion.div
          animate={faceAnimate}
          transition={faceTransition}
          className="absolute inset-0"
        >
          <div className={`absolute inset-0 origin-center ${small ? 'scale-[0.26]' : 'scale-100'}`}>
            <Eyes tone={effectiveTone} />

            <div className="absolute inset-0 flex items-center justify-center pt-10">
              <Mouth tone={effectiveTone} />
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

const Blob = memo(BlobBase)

export default Blob
