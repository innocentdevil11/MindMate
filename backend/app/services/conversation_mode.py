"""
Conversation Mode Detector — MindMate v3.

Detects user-requested conversation mode overrides.
Runs BEFORE agent routing to prevent unwanted mentoring/advice
when the user explicitly asks for casual chat.

Modes:
  normal          — default, full pipeline
  casual_chat     — disable problem-solving agents, respond like a friend
  problem_solving — user explicitly asked for help/advice (re-enable agents)
  reflection      — reserved for future use
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ========================= TRIGGER PHRASES =========================

# Phrases that switch INTO casual_chat mode
_CASUAL_TRIGGERS = [
    r"\bjust talk\b",
    r"\bjust chat\b",
    r"\bdon'?t\s+(give\s+)?(me\s+)?advice\b",
    r"\bdon'?t\s+advise\b",
    r"\bdon'?t\s+mentor\b",
    r"\bdon'?t\s+lecture\b",
    r"\bstop\s+(giving\s+)?(me\s+)?advice\b",
    r"\bstop\s+lecturing\b",
    r"\bstop\s+mentoring\b",
    r"\bnot\s+looking\s+for\s+solutions?\b",
    r"\bdon'?t\s+act\s+like\s+(a|my)\s+mentor\b",
    r"\bno\s+advice\b",
    r"\bno\s+lectures?\b",
    r"\bjust\s+be\s+normal\b",
    r"\btalk\s+to\s+me\s+(like\s+)?(a\s+)?(friend|human|person)\b",
    r"\bdon'?t\s+coach\b",
    r"\bstop\s+coaching\b",
]

# Phrases that switch OUT of casual_chat back to problem_solving
_SOLVE_TRIGGERS = [
    r"\bwhat\s+should\s+i\s+do\b",
    r"\bgive\s+me\s+advice\b",
    r"\bhelp\s+me\s+plan\b",
    r"\bactually\s+help\b",
    r"\bok\s+advise\s+me\b",
    r"\bcan\s+you\s+help\b",
    r"\bi\s+need\s+(your\s+)?help\b",
    r"\bgive\s+me\s+(a\s+)?plan\b",
    r"\badvise\s+me\b",
    r"\bwhat\s+do\s+you\s+suggest\b",
    r"\bwhat\s+do\s+you\s+think\s+i\s+should\b",
    r"\bhelp\s+me\s+(figure|work)\b",
]

_CASUAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _CASUAL_TRIGGERS]
_SOLVE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _SOLVE_TRIGGERS]


# ========================= DETECTOR =========================

def detect_mode_override(
    user_query: str,
    current_mode: str = "normal",
) -> str:
    """
    Detect if user message contains an explicit conversation mode override.

    Args:
        user_query: The user's current message text.
        current_mode: The previously-active conversation mode.

    Returns:
        Updated conversation mode string.
    """
    text = user_query.strip()

    # Check for casual-chat triggers
    for pattern in _CASUAL_PATTERNS:
        if pattern.search(text):
            logger.info(f"Detected conversation override → casual_chat (trigger matched in: '{text[:80]}')")
            return "casual_chat"

    # Check for problem-solving re-engagement triggers
    for pattern in _SOLVE_PATTERNS:
        if pattern.search(text):
            if current_mode == "casual_chat":
                logger.info(f"Detected conversation override → problem_solving (exit casual_chat)")
            return "problem_solving"

    # No override detected, keep current mode
    # But if current mode is problem_solving and no explicit signal, revert to normal
    if current_mode == "problem_solving":
        return "normal"

    return current_mode


# ========================= PROMPT HELPERS =========================

CASUAL_CHAT_SYSTEM_RULES = (
    "CONVERSATION MODE: CASUAL CHAT\n"
    "The user has explicitly asked you NOT to give advice, plans, or mentoring.\n"
    "STRICT RULES:\n"
    "- Respond like a human friend in a casual text chat.\n"
    "- Keep responses to 1-3 sentences max.\n"
    "- DO NOT give structured advice, study plans, or step-by-step solutions.\n"
    "- DO NOT use coaching language like: 'we need a plan', 'let's break this down', "
    "'set clear goals', 'create actionable steps', 'listen up', 'first, second, third'.\n"
    "- DO NOT format responses with bullet points or numbered lists.\n"
    "- Be short, friendly, reactive, and curious.\n"
    "- Match the user's energy. If they're venting, acknowledge it.\n"
    "- It's OK to be a little witty or playful.\n"
    "- If the user asks a question, engage with it conversationally, not didactically.\n"
)
