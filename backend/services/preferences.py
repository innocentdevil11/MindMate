"""
Preferences service — MindMate.

Manages user-scoped preferences (tone, default weights).
All operations require a user_id from the auth dependency.

WHY upsert: A user may not have a preferences row yet (first visit).
Upsert creates on first access, updates on subsequent changes.
"""

import logging
from db import get_supabase_admin

logger = logging.getLogger(__name__)

# Valid tone values — "blunt_profane" requires explicit opt-in
VALID_TONES = ("clean", "casual", "blunt", "blunt_profane")

# Default weights matching the existing frontend slider defaults
DEFAULT_WEIGHTS = {
    "ethical": 0.2,
    "risk": 0.2,
    "eq": 0.2,
    "values": 0.2,
    "red_team": 0.2,
}


async def get_preferences(user_id: str) -> dict:
    """
    Fetch user preferences. Returns defaults if no row exists yet.

    Returns:
        dict with keys: tone_preference, default_weights
    """
    sb = get_supabase_admin()
    result = (
        sb.table("user_preferences")
        .select("tone_preference, default_weights")
        .eq("user_id", user_id)
        .execute()
    )

    if result.data and len(result.data) > 0:
        return result.data[0]

    # No row yet — return defaults (row will be created on first update)
    return {
        "tone_preference": "clean",
        "default_weights": DEFAULT_WEIGHTS,
    }


async def update_preferences(user_id: str, data: dict) -> dict:
    """
    Upsert user preferences.

    Args:
        data: dict with optional keys: tone_preference, default_weights

    Returns:
        Updated preferences dict

    Raises:
        ValueError: If tone_preference is invalid
    """
    tone = data.get("tone_preference")
    if tone and tone not in VALID_TONES:
        raise ValueError(
            f"Invalid tone_preference '{tone}'. Must be one of: {VALID_TONES}"
        )

    # Build upsert payload
    payload = {"user_id": user_id}
    if tone:
        payload["tone_preference"] = tone
    if "default_weights" in data:
        payload["default_weights"] = data["default_weights"]

    sb = get_supabase_admin()
    result = (
        sb.table("user_preferences")
        .upsert(payload, on_conflict="user_id")
        .execute()
    )

    logger.info(f"Preferences updated for user {user_id[:8]}...")
    return result.data[0] if result.data else payload
