"""
Complexity Classifier — MindMate v3.

Determines reasoning depth required for a query.
Uses heuristics first (token-free), LLM fallback for ambiguous cases.

Routing:
  simple  → direct response, no agents, no debate
  medium  → multi-agent reasoning, no debate
  complex → multi-agent reasoning + debate
"""

import logging
from app.models.schemas import Intent, Complexity, ComplexityResult

logger = logging.getLogger(__name__)

# Intents that are always simple (no reasoning needed)
_SIMPLE_INTENTS = {
    Intent.GREETING,
    Intent.SMALLTALK,
    Intent.GRATITUDE,
    Intent.CLOSING,
}

# Intents that always require full multi-agent reasoning
_COMPLEX_INTENTS = {
    Intent.DEEP_PROBLEM,
}

# Intents that go to medium by default
_MEDIUM_INTENTS = {
    Intent.ADVICE_REQUEST,
    Intent.EMOTIONAL_DISTRESS,
    Intent.FRUSTRATION,
    Intent.REFLECTION,
}

# Word count thresholds
_SHORT_MESSAGE_THRESHOLD = 8    # ≤ 8 words = likely simple
_LONG_MESSAGE_THRESHOLD = 40    # ≥ 40 words = likely complex

# Keywords that signal complexity
_COMPLEXITY_SIGNALS = {
    "should i", "what should", "help me decide", "i'm torn",
    "on one hand", "pros and cons", "dilemma", "struggling with",
    "i don't know what to do", "advice", "what would you do",
    "is it worth", "trade-off", "complicated", "conflicted",
}


def classify_complexity(
    query: str,
    intent: Intent,
    conversation_depth: int = 0,
) -> ComplexityResult:
    """
    Classify the reasoning complexity needed for this query.

    Uses a deterministic heuristic pipeline (no LLM call needed).
    This saves tokens and adds zero latency.

    Args:
        query: The user's message
        intent: Previously classified intent
        conversation_depth: Number of messages in current conversation

    Returns:
        ComplexityResult with complexity level and reasoning
    """
    query_lower = query.lower()
    word_count = len(query.split())

    # Rule 1: Simple intents are always simple
    if intent in _SIMPLE_INTENTS:
        return ComplexityResult(
            complexity=Complexity.SIMPLE,
            reasoning=f"Intent '{intent.value}' is inherently simple"
        )

    # Rule 2: Deep problems are always complex
    if intent in _COMPLEX_INTENTS:
        return ComplexityResult(
            complexity=Complexity.COMPLEX,
            reasoning=f"Intent '{intent.value}' requires full multi-agent debate"
        )

    # Rule 3: Check for complexity signal keywords
    has_complexity_signal = any(signal in query_lower for signal in _COMPLEXITY_SIGNALS)

    # Rule 4: Factual questions are simple unless they're long or have complexity signals
    if intent == Intent.FACTUAL_QUESTION:
        if has_complexity_signal or word_count >= _LONG_MESSAGE_THRESHOLD:
            return ComplexityResult(
                complexity=Complexity.MEDIUM,
                reasoning="Factual question with complexity signals or long length"
            )
        return ComplexityResult(
            complexity=Complexity.SIMPLE,
            reasoning="Straightforward factual question"
        )

    # Rule 5: Follow-ups inherit complexity from conversation depth
    if intent == Intent.FOLLOW_UP:
        if conversation_depth > 6 or has_complexity_signal:
            return ComplexityResult(
                complexity=Complexity.COMPLEX,
                reasoning="Deep follow-up in extended conversation"
            )
        return ComplexityResult(
            complexity=Complexity.MEDIUM,
            reasoning="Follow-up continues ongoing reasoning"
        )

    # Rule 6: Medium intents can be upgraded to complex
    if intent in _MEDIUM_INTENTS:
        if has_complexity_signal and word_count >= _LONG_MESSAGE_THRESHOLD:
            return ComplexityResult(
                complexity=Complexity.COMPLEX,
                reasoning="Long message with explicit complexity signals"
            )
        if has_complexity_signal or word_count >= _LONG_MESSAGE_THRESHOLD:
            return ComplexityResult(
                complexity=Complexity.MEDIUM,
                reasoning="Advice/emotional query needing multi-agent reasoning"
            )
        # Short advice/emotional messages are still medium
        return ComplexityResult(
            complexity=Complexity.MEDIUM,
            reasoning=f"Intent '{intent.value}' defaults to medium complexity"
        )

    # Default: medium
    return ComplexityResult(
        complexity=Complexity.MEDIUM,
        reasoning="Default classification for ambiguous queries"
    )
