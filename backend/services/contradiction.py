"""
Contradiction Detection service — MindMate.

Simple rule-based checker that flags when new preferences or memory
contradict existing ones. Does NOT overwrite — flags for user clarification.

WHY rule-based: No ML classifiers needed. Contradictions in preferences
are detectable via simple value comparison (e.g., clean → blunt_profane).
"""

import logging
from db import get_supabase_admin

logger = logging.getLogger(__name__)

# Tone contradiction pairs — these transitions are suspicious
_TONE_CONTRADICTIONS = {
    ("clean", "blunt_profane"),
    ("blunt_profane", "clean"),
    ("clean", "blunt"),
    ("blunt", "clean"),
}


async def check_preference_contradiction(
    user_id: str,
    field: str,
    new_value: str,
) -> dict:
    """
    Check if updating a preference field contradicts the current value.

    Args:
        field: The preference field being updated (e.g., 'tone_preference')
        new_value: The proposed new value

    Returns:
        {
            "conflict": bool,
            "existing_value": str | None,
            "message": str | None,
        }
    """
    sb = get_supabase_admin()
    result = (
        sb.table("user_preferences")
        .select(field)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data or len(result.data) == 0:
        # No existing preference — no contradiction possible
        return {"conflict": False, "existing_value": None, "message": None}

    existing_value = result.data[0].get(field)

    if existing_value == new_value:
        return {"conflict": False, "existing_value": existing_value, "message": None}

    # Check tone-specific contradictions
    if field == "tone_preference":
        pair = (existing_value, new_value)
        if pair in _TONE_CONTRADICTIONS:
            msg = (
                f"Your current tone is '{existing_value}' but you're switching to "
                f"'{new_value}'. This is a significant change. Are you sure?"
            )
            logger.info(f"Contradiction detected for user {user_id[:8]}: {pair}")
            return {"conflict": True, "existing_value": existing_value, "message": msg}

    # Non-contradictory change
    return {"conflict": False, "existing_value": existing_value, "message": None}


async def check_memory_contradiction(
    user_id: str,
    memory_type: str,
    label: str,
    new_content: str,
) -> dict:
    """
    Check if a new memory entry contradicts an existing one with the same label.

    WHY: If a user previously said "I'm risk-averse" and now says "I love risk",
    we should flag this rather than silently overwriting.

    Returns:
        {
            "conflict": bool,
            "existing_content": str | None,
            "message": str | None,
        }
    """
    sb = get_supabase_admin()
    result = (
        sb.table("user_memory")
        .select("content, confidence")
        .eq("user_id", user_id)
        .eq("type", memory_type)
        .eq("label", label)
        .gte("confidence", 0.3)
        .order("confidence", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        return {"conflict": False, "existing_content": None, "message": None}

    existing = result.data[0]
    existing_content = existing["content"]

    # Simple heuristic: if existing and new content are substantially different,
    # flag as potential contradiction. We compare lowercased strings.
    # A more sophisticated approach could use embeddings, but rule-based is spec.
    if existing_content.lower().strip() != new_content.lower().strip():
        msg = (
            f"You previously noted '{label}' as: \"{existing_content}\". "
            f"The new input suggests: \"{new_content}\". "
            f"Would you like to update or keep the original?"
        )
        return {"conflict": True, "existing_content": existing_content, "message": msg}

    return {"conflict": False, "existing_content": existing_content, "message": None}
