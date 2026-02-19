"""
Feedback service — MindMate.

Handles user feedback on response quality and applies policy adjustments
(NOT model retraining). Requires consistent signals before making changes.

WHY threshold-based: A single bad feedback shouldn't change behavior.
Only after 3+ consistent signals do we adjust tone strength or defaults.
"""

import logging
from db import get_supabase_admin

logger = logging.getLogger(__name__)

# How many consistent feedback signals before applying an adjustment
CONSISTENCY_THRESHOLD = 3

VALID_TONE_ALIGNMENTS = ("too_soft", "just_right", "too_harsh")
VALID_OUTCOMES = ("helped", "didnt_help")


async def store_feedback(
    user_id: str,
    query: str,
    tone_alignment: str = None,
    usefulness: int = None,
    outcome: str = None,
) -> dict:
    """
    Store a feedback entry for a decision response.

    Args:
        query: The original user query this feedback refers to
        tone_alignment: 'too_soft', 'just_right', or 'too_harsh'
        usefulness: 1–10 rating
        outcome: 'helped' or 'didnt_help'
    """
    # Validate
    if tone_alignment and tone_alignment not in VALID_TONE_ALIGNMENTS:
        raise ValueError(f"Invalid tone_alignment. Must be one of: {VALID_TONE_ALIGNMENTS}")
    if usefulness is not None and not (1 <= usefulness <= 10):
        raise ValueError("usefulness must be between 1 and 10")
    if outcome and outcome not in VALID_OUTCOMES:
        raise ValueError(f"Invalid outcome. Must be one of: {VALID_OUTCOMES}")

    payload = {"user_id": user_id, "query": query}
    if tone_alignment:
        payload["tone_alignment"] = tone_alignment
    if usefulness is not None:
        payload["usefulness"] = usefulness
    if outcome:
        payload["outcome"] = outcome

    sb = get_supabase_admin()
    result = sb.table("user_feedback").insert(payload).execute()

    logger.info(f"Feedback stored for user {user_id[:8]}...")
    return result.data[0] if result.data else {}


async def compute_adjustments(user_id: str) -> dict:
    """
    Analyze recent feedback to determine if policy adjustments are warranted.

    Only applies changes after CONSISTENCY_THRESHOLD (3) consistent signals.
    This prevents a single outlier from changing behavior.

    Returns:
        {
            "tone_adjustment": str | None,  # 'softer', 'harsher', or None
            "confidence": float,            # 0.0 - 1.0
            "signal_count": int,
        }
    """
    sb = get_supabase_admin()

    # Fetch last 10 feedback entries for this user
    result = (
        sb.table("user_feedback")
        .select("tone_alignment, usefulness, outcome")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )

    feedback_list = result.data or []

    if len(feedback_list) < CONSISTENCY_THRESHOLD:
        return {"tone_adjustment": None, "confidence": 0.0, "signal_count": len(feedback_list)}

    # Count tone alignment signals
    too_soft_count = sum(1 for f in feedback_list if f.get("tone_alignment") == "too_soft")
    too_harsh_count = sum(1 for f in feedback_list if f.get("tone_alignment") == "too_harsh")
    total_tone = too_soft_count + too_harsh_count

    tone_adjustment = None
    confidence = 0.0

    if too_soft_count >= CONSISTENCY_THRESHOLD:
        tone_adjustment = "harsher"
        confidence = too_soft_count / max(total_tone, 1)
    elif too_harsh_count >= CONSISTENCY_THRESHOLD:
        tone_adjustment = "softer"
        confidence = too_harsh_count / max(total_tone, 1)

    return {
        "tone_adjustment": tone_adjustment,
        "confidence": round(confidence, 2),
        "signal_count": len(feedback_list),
    }
