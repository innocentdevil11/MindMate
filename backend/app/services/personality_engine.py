"""
Personality Style Engine — MindMate v3 (FIXED).

Now blends TWO layers:
  1. Brain dominance → shapes WHAT the AI emphasizes (logic vs empathy vs values)
  2. User tone mode → shapes HOW the AI speaks (clean vs casual vs blunt vs unfiltered)

Previously only the brain layer existed with a 0.35 threshold that
was rarely triggered. Now the threshold is 0.25 and tone mode is always active.
"""

import logging
from app.models.schemas import AgentName, BrainConfig
from app.services.brain_engine import normalize_weights

logger = logging.getLogger(__name__)

# ========================= LAYER 1: BRAIN DOMINANCE =========================
# What the AI emphasizes based on which agent is strongest

_BRAIN_RULES = {
    AgentName.EMOTIONAL: {
        "style": "empathetic",
        "instruction": (
            "Lead with empathy and emotional attunement. "
            "Show you understand their feelings. "
            "Be gentle and caring. Validate their emotions first."
        ),
    },
    AgentName.ANALYTICAL: {
        "style": "logical",
        "instruction": (
            "Lead with clear logic and structured reasoning. "
            "Be direct and precise. Present facts first, feelings second. "
            "Be actionable and concise."
        ),
    },
    AgentName.RED_TEAM: {
        "style": "challenger",
        "instruction": (
            "Challenge assumptions directly. Play devil's advocate. "
            "Ask uncomfortable but constructive questions. "
            "Push the user to think deeper."
        ),
    },
    AgentName.VALUES: {
        "style": "philosophical",
        "instruction": (
            "Reflect on identity and deeper meaning. "
            "Frame choices in terms of who they want to become. "
            "Be thoughtful and introspective. "
            "CRITICAL: Speak naturally and conversationally. Avoid overly poetic or dramatic phrasing. "
            "Avoid abstract philosophical monologues unless explicitly requested. "
            "Filter examples to avoid: 'the depths of identity', 'embody your true self', 'contemplative space'."
        ),
    },
    AgentName.ETHICAL: {
        "style": "wise",
        "instruction": (
            "Speak with grounded moral wisdom. "
            "Reference principles of right action. "
            "Be calm, measured, and authoritative."
        ),
    },
}

_BALANCED_BRAIN = (
    "Balance empathy with logic. "
    "Be warm but direct. Feel like a thoughtful friend."
)

# ========================= LAYER 2: TONE MODE =========================
# HOW the AI speaks — controlled by user's tone buttons

_TONE_MODES = {
    "clean": {
        "label": "Clean",
        "instruction": (
            "Use polished, professional language. "
            "No slang. No profanity. Grammatically correct. "
            "Warm but composed."
        ),
    },
    "casual": {
        "label": "Casual",
        "instruction": (
            "Talk like a close friend. Use contractions, casual phrasing. "
            "It's okay to use 'yeah', 'honestly', 'look', 'tbh'. "
            "Relaxed but still respectful. No stiffness."
        ),
    },
    "blunt": {
        "label": "Blunt",
        "instruction": (
            "Be brutally honest and direct. No sugar-coating. "
            "Cut the fluff. Say what needs to be said. "
            "Short sentences. No unnecessary qualifiers."
        ),
    },
    "blunt_profane": {
        "label": "Unfiltered",
        "instruction": (
            "Speak raw and unfiltered. Swear if it fits. "
            "Talk like a real person who doesn't care about being polished. "
            "Be genuine above all else. No corporate-speak. "
            "Use 'damn', 'hell', etc naturally. Still be helpful."
        ),
    },
    "mentor": {
        "label": "Mentor",
        "instruction": (
            "Sound like a thoughtful coach. Structure advice into clear steps. "
            "Be encouraging, specific, and actionable. "
            "Reassure while challenging the user to grow."
        ),
    },
    "philosophical": {
        "label": "Philosophical",
        "instruction": (
            "Be reflective and values-oriented, but speak naturally. "
            "Use calm, contemplative language that explores meaning without being melodramatic. "
            "Offer gentle prompts that invite introspection. "
            "Avoid overly poetic, theatrical, or abstract monologues. Keep it human and grounded."
        ),
    },
    "supportive": {
        "label": "Supportive",
        "instruction": (
            "Be warm, empathetic, and reassuring. "
            "Affirm the user's feelings and safety. "
            "Use gentle, kind phrasing; avoid harshness."
        ),
    },
}


def get_personality_tone(
    brain_config: BrainConfig,
    tone_mode: str = "clean",
) -> str:
    """
    Generate combined tone instructions from brain dominance + user tone mode.

    Args:
        brain_config: User's agent weights
        tone_mode: User-selected tone (clean/casual/blunt/blunt_profane)

    Returns:
        Full tone instruction string for prompt injection.
    """
    # Layer 1: Brain dominance (normalize then pick max)
    normalized = normalize_weights(brain_config.model_dump())
    dominant_key = max(normalized, key=normalized.get)

    # Fallback to analytical if somehow missing
    dominant_enum = AgentName(dominant_key) if dominant_key in AgentName._value2member_map_ else AgentName.ANALYTICAL

    brain_info = _BRAIN_RULES[dominant_enum]
    brain_instruction = brain_info["instruction"]
    brain_style = brain_info["style"]

    # Layer 2: Tone mode
    tone_info = _TONE_MODES.get(tone_mode, _TONE_MODES["clean"])
    tone_instruction = tone_info["instruction"]

    combined = (
        f"[PERSONALITY: {brain_style.upper()}] {brain_instruction}\n"
        f"[TONE: {tone_mode.upper()}] {tone_instruction}"
    )

    logger.info(f"Dominant agent: {dominant_enum.value} (weights={normalized})")
    logger.info(f"Tone mode: {tone_mode}")
    return combined


def get_style_name(brain_config: BrainConfig) -> str:
    """Get a human-readable style name for UI display."""
    normalized = normalize_weights(brain_config.model_dump())
    dominant_key = max(normalized, key=normalized.get)
    dominant_enum = AgentName(dominant_key) if dominant_key in AgentName._value2member_map_ else AgentName.ANALYTICAL

    return _BRAIN_RULES[dominant_enum]["style"].title()
