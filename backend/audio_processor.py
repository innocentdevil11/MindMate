"""
Audio transcription module using OpenAI's free Whisper model (locally).
Supports real-time transcription with streaming and caching - NO API COSTS.
"""

import os
from typing import Optional, Dict, AsyncGenerator
import whisper
import whisper.audio
import asyncio
from functools import lru_cache
import hashlib
import numpy as np
import io
import tempfile

# Initialize Whisper model (loads once, cached)
_whisper_model = None

def get_whisper_model(model_size: str = "base"):
    """
    Load Whisper model lazily. Uses 'base' by default for balance.
    
    Model sizes (in GB):
    - tiny: 39MB (fastest, less accurate)
    - base: 139MB (recommended)
    - small: 466MB (better accuracy)
    - medium: 1.5GB (high accuracy)
    - large: 3.1GB (best accuracy, slow)
    """
    global _whisper_model
    if _whisper_model is None:
        print(f"Loading Whisper {model_size} model (first load may take a moment)...")
        _whisper_model = whisper.load_model(model_size)
    return _whisper_model

# Cache for transcription results (in-memory)
transcription_cache: Dict[str, str] = {}


def get_audio_hash(audio_bytes: bytes) -> str:
    """Generate hash of audio bytes for caching."""
    return hashlib.md5(audio_bytes).hexdigest()


def transcribe_audio(audio_bytes: bytes, language: Optional[str] = None, model_size: str = "base") -> Dict:
    """
    Transcribe audio bytes to text using FREE local Whisper model.
    No API keys, no costs, runs locally!
    
    Args:
        audio_bytes: Raw audio data in bytes (supports WAV, MP3, MP4, WebM, etc.)
        language: Optional language code (e.g., 'en', 'es', 'fr') - auto-detects if None
        model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
    
    Returns:
        Dict with 'text' (transcribed text) and 'language' fields
    """
    try:
        print(f"[AUDIO] Starting transcription: {len(audio_bytes)} bytes, language={language}, model={model_size}")
        
        # Check cache first
        audio_hash = get_audio_hash(audio_bytes)
        if audio_hash in transcription_cache:
            print(f"[AUDIO] Cache hit! Returning cached result")
            return {
                "text": transcription_cache[audio_hash],
                "language": language or "en",
                "cached": True,
                "model": model_size
            }
        
        # Get Whisper model
        print(f"[AUDIO] Loading Whisper model: {model_size}")
        model = get_whisper_model(model_size)
        print(f"[AUDIO] Model loaded successfully")
        
        # Save audio bytes to temporary file (Whisper needs file path or numpy array)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            print(f"[AUDIO] Loading audio from temporary file: {tmp_path}")
            # Load audio using Whisper's audio module (handles format conversion, resampling)
            audio_data = whisper.audio.load_audio(tmp_path)
            print(f"[AUDIO] Audio loaded: shape={audio_data.shape}")
            
            print(f"[AUDIO] Starting model.transcribe()...")
            # Transcribe with optional language specification
            result = model.transcribe(
                audio_data,
                language=language,
                verbose=False,  # Suppress debug output
                fp16=False  # Use fp32 for compatibility
            )
            print(f"[AUDIO] Transcription complete")
            
            text = result["text"].strip()
            detected_language = result.get("language", language or "en")
            
            # Cache the result
            transcription_cache[audio_hash] = text
            print(f"[AUDIO] Result: '{text}'")
            
            return {
                "text": text,
                "language": detected_language,
                "cached": False,
                "model": model_size,
                "confidence": "high"
            }
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    except Exception as e:
        error_msg = f"Transcription exception: {str(e)}"
        print(f"[AUDIO ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            "error": error_msg,
            "text": "",
            "language": language or "en",
            "model": model_size
        }


async def transcribe_audio_async(audio_bytes: bytes, language: Optional[str] = None, model_size: str = "base") -> Dict:
    """
    Async wrapper for audio transcription to prevent blocking main thread.
    Runs transcription in thread pool executor.
    
    Args:
        audio_bytes: Raw audio data in bytes
        language: Optional language code
        model_size: Whisper model size
    
    Returns:
        Dict with transcription result
    """
    try:
        print(f"[TRANSCRIBE] Starting async transcription: {len(audio_bytes)} bytes, language={language}, model={model_size}")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, transcribe_audio, audio_bytes, language, model_size)
        print(f"[TRANSCRIBE] Result: {result}")
        return result
    except Exception as e:
        error_msg = f"Async transcription error: {str(e)}"
        print(f"[TRANSCRIBE ERROR] {error_msg}")
        return {
            "text": "",
            "error": error_msg,
            "language": language or "en"
        }


def clear_cache():
    """Clear transcription cache."""
    global transcription_cache
    transcription_cache.clear()


def get_cache_stats() -> Dict:
    """Get cache statistics."""
    return {
        "cached_items": len(transcription_cache),
        "cache_size_kb": sum(len(v.encode()) for v in transcription_cache.values()) / 1024
    }
