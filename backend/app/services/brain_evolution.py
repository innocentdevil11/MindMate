"""
Brain Evolution Engine — MindMate v3.

Learns preferred brain weights from feedback over time.
High-rated conversations contribute their brain config to a weighted average.

This creates a user preference model:
  - Conversations rated 4-5 stars: their brain config gets MORE weight
  - Conversations rated 1-2 stars: their brain config gets LESS weight
  - Future conversations start with these evolved defaults

No ML, no retraining — just weighted averaging of explicit feedback signals.
"""

import logging
from typing import Optional, Dict

from db import get_supabase_admin
from app.models.schemas import BrainConfig

logger = logging.getLogger(__name__)

# Minimum feedback entries before evolution kicks in
MIN_FEEDBACK_FOR_EVOLUTION = 3

# Rating-to-weight mapping: higher ratings = more influence
_RATING_WEIGHTS = {
    1: 0.1,   # Very low influence
    2: 0.3,
    3: 0.5,   # Neutral
    4: 0.8,
    5: 1.0,   # Full influence
}

# Agent weight keys
_AGENT_KEYS = ["analytical", "emotional", "ethical", "values", "red_team"]


async def compute_evolved_defaults(user_id: str) -> Optional[BrainConfig]:
    """
    Compute the user's preferred brain weights from feedback history.

    Algorithm:
      1. Fetch all feedback_v2 entries with brain_config snapshots
      2. Weight each config by its rating (5-star configs matter more)
      3. Normalize to get the evolved default weights
      4. Store in evolved_brain_defaults table

    Returns:
        BrainConfig if enough data, None otherwise
    """
    sb = get_supabase_admin()

    # Fetch feedback with brain configs
    result = (
        sb.table("feedback_v2")
        .select("rating, brain_config")
        .eq("user_id", user_id)
        .not_.is_("brain_config", "null")
        .order("created_at", desc=True)
        .limit(50)  # Use last 50 feedback entries
        .execute()
    )

    entries = result.data or []
    if len(entries) < MIN_FEEDBACK_FOR_EVOLUTION:
        logger.debug(f"Not enough feedback for evolution ({len(entries)}/{MIN_FEEDBACK_FOR_EVOLUTION})")
        return None

    # Weighted accumulation
    weighted_sums = {k: 0.0 for k in _AGENT_KEYS}
    total_weight = 0.0

    for entry in entries:
        rating = entry.get("rating", 3)
        config = entry.get("brain_config", {})

        if not config:
            continue

        weight = _RATING_WEIGHTS.get(rating, 0.5)
        total_weight += weight

        for key in _AGENT_KEYS:
            weighted_sums[key] += config.get(key, 0.2) * weight

    if total_weight == 0:
        return None

    # Normalize: divide by total weight to get average, then normalize to sum=1
    raw_weights = {k: weighted_sums[k] / total_weight for k in _AGENT_KEYS}
    weight_sum = sum(raw_weights.values())

    if weight_sum == 0:
        return None

    normalized = {k: round(v / weight_sum, 3) for k, v in raw_weights.items()}

    evolved_config = BrainConfig(**normalized)

    # Store the evolved defaults
    await _store_evolved_defaults(user_id, evolved_config, len(entries))

    logger.info(f"Brain evolution computed for user {user_id[:8]}: {normalized}")
    return evolved_config


async def _store_evolved_defaults(
    user_id: str,
    config: BrainConfig,
    sample_count: int,
) -> None:
    """Store/update the evolved brain defaults for a user."""
    sb = get_supabase_admin()
    sb.table("evolved_brain_defaults").upsert(
        {
            "user_id": user_id,
            "preferred_weights": config.model_dump(),
            "sample_count": sample_count,
        },
        on_conflict="user_id",
    ).execute()


async def get_evolution_status(user_id: str) -> Dict:
    """Get the current brain evolution status for a user."""
    sb = get_supabase_admin()

    # Check current evolved defaults
    evolved = (
        sb.table("evolved_brain_defaults")
        .select("preferred_weights, sample_count, updated_at")
        .eq("user_id", user_id)
        .execute()
    )

    # Count total feedback
    feedback_count = (
        sb.table("feedback_v2")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )

    return {
        "has_evolved": bool(evolved.data),
        "current_defaults": evolved.data[0] if evolved.data else None,
        "total_feedback_count": feedback_count.count or 0,
        "min_feedback_required": MIN_FEEDBACK_FOR_EVOLUTION,
    }
