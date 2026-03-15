"""
Intent Classifier — MindMate v3.

Lightweight LLM-based classification of user intent.
Uses Groq with minimal tokens (max_tokens=30) to classify
into one of 11 predefined intents.

Token budget: ~150 input + 30 output = ~180 tokens per call.
"""

import json
import logging
from typing import Optional

from app.models.schemas import Intent, IntentResult

logger = logging.getLogger(__name__)

# Compact classification prompt — optimized for token efficiency
_CLASSIFIER_PROMPT = """Classify the user message into exactly ONE intent.

Intents: greeting, smalltalk, emotional_distress, frustration, follow_up, deep_problem, advice_request, factual_question, reflection, gratitude, closing

Rules:
- greeting: hi/hello/hey
- smalltalk: casual chat, weather, how are you
- emotional_distress: sadness, anxiety, pain, crisis
- frustration: anger, annoyance, venting
- follow_up: continues previous topic, "what about", "and also"
- deep_problem: complex life/work/relationship dilemma
- advice_request: "should I", "what do you think", seeking guidance
- factual_question: asking for facts, definitions, how-to
- reflection: thinking aloud, journaling, self-analysis
- gratitude: thanks, appreciation
- closing: bye, goodbye, end conversation

Respond with ONLY a JSON object: {"intent": "<intent>", "confidence": <0.0-1.0>}"""

# Intents that can be detected without LLM (keyword-based fast path)
_GREETING_KEYWORDS = {"hi", "hello", "hey", "yo", "sup", "hiya", "howdy"}
_CLOSING_KEYWORDS = {"bye", "goodbye", "see ya", "later", "cya", "goodnight", "good night"}
_GRATITUDE_KEYWORDS = {"thank", "thanks", "thx", "appreciate", "grateful"}


def _fast_classify(query: str) -> Optional[IntentResult]:
    """
    Rule-based fast path for obvious intents.
    Avoids an LLM call for simple greetings, closings, gratitude.
    Returns None if heuristic is not confident.
    """
    words = set(query.lower().strip().rstrip("!?.").split())

    # Single-word or two-word messages are often greetings/closings
    if len(words) <= 3:
        if words & _GREETING_KEYWORDS:
            return IntentResult(intent=Intent.GREETING, confidence=0.95)
        if words & _CLOSING_KEYWORDS:
            return IntentResult(intent=Intent.CLOSING, confidence=0.95)

    # Gratitude can appear in longer messages
    if words & _GRATITUDE_KEYWORDS and len(words) <= 6:
        return IntentResult(intent=Intent.GRATITUDE, confidence=0.90)

    return None


def classify_intent(query: str, call_groq_fn) -> IntentResult:
    """
    Classify user intent. Tries fast path first, falls back to LLM.

    Args:
        query: The user's message
        call_groq_fn: Callable that takes (system_prompt, user_message, **kwargs) -> str
                      Injected to avoid circular imports with groq_client.

    Returns:
        IntentResult with intent enum and confidence score
    """
    # Fast path — skip LLM for obvious intents
    fast_result = _fast_classify(query)
    if fast_result:
        logger.debug(f"Fast-classified intent: {fast_result.intent.value}")
        return fast_result

    # LLM classification
    try:
        raw = call_groq_fn(
            system_prompt=_CLASSIFIER_PROMPT,
            user_message=query,
            temperature=0.1,
            max_tokens=30,
        )

        # Parse JSON response
        parsed = json.loads(raw.strip())
        intent_str = parsed.get("intent", "").lower().strip()
        confidence = float(parsed.get("confidence", 0.5))

        # Validate intent enum
        try:
            intent = Intent(intent_str)
        except ValueError:
            logger.warning(f"Unknown intent '{intent_str}', defaulting to smalltalk")
            intent = Intent.SMALLTALK
            confidence = 0.3

        return IntentResult(intent=intent, confidence=confidence)

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Intent classification parse error: {e}, defaulting to advice_request")
        return IntentResult(intent=Intent.ADVICE_REQUEST, confidence=0.3)
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        return IntentResult(intent=Intent.ADVICE_REQUEST, confidence=0.2)
