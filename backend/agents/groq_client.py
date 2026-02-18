"""
Shared Groq API client for all MindMate agents.
Centralizes the Groq SDK initialization and provides a simple call interface.
Includes retry logic for rate limit handling.
"""

import os
import time
import random
import logging
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

logger = logging.getLogger(__name__)

# ================= ENV SETUP =================
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
dotenv_path = backend_dir / '.env'
load_dotenv(dotenv_path=dotenv_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Singleton client
_client = None


def get_groq_client() -> Groq:
    """Get or create the Groq client instance."""
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY not set. Add it to backend/.env file."
            )
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def call_groq(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 700,
    model: str = None,
) -> str:
    """
    Make a chat completion call to Groq with automatic retry on rate limits.

    Retries up to 3 times with exponential backoff + jitter when rate limited.
    """
    client = get_groq_client()
    max_retries = 3

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model or GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = "rate_limit" in error_str or "429" in error_str or "too many" in error_str

            if is_rate_limit and attempt < max_retries:
                # Exponential backoff: 2s, 4s, 8s + random jitter
                wait_time = (2 ** (attempt + 1)) + random.uniform(0.5, 2.0)
                logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}), waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Groq API error: {e}")
                raise
