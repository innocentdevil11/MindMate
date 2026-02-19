"""
Structured Memory service — MindMate.

Stores and retrieves user memories with type, confidence, and decay.
No raw chat logs — only structured entries (preference, pattern, outcome).

WHY confidence decay: Old unused memories should fade naturally.
This prevents stale patterns from dominating current interactions.
"""

import logging
from datetime import datetime, timezone
from db import get_supabase_admin

logger = logging.getLogger(__name__)

# Memory types — strict enum
VALID_MEMORY_TYPES = ("preference", "pattern", "outcome")

# Decay config
CONFIDENCE_DECAY_RATE = 0.05  # Reduce by 5% per decay cycle
MIN_RETRIEVAL_CONFIDENCE = 0.3  # Ignore memories below this


async def store_memory(
    user_id: str,
    memory_type: str,
    label: str,
    content: str,
    confidence: float = 1.0,
) -> dict:
    """
    Store a structured memory entry.

    Args:
        memory_type: One of 'preference', 'pattern', 'outcome'
        label: Short descriptor (e.g., "overthinking", "risk_averse")
        content: Longer description of the memory
        confidence: Initial confidence score (0.0 - 1.0)
    """
    if memory_type not in VALID_MEMORY_TYPES:
        raise ValueError(
            f"Invalid memory type '{memory_type}'. Must be one of: {VALID_MEMORY_TYPES}"
        )
    confidence = max(0.0, min(1.0, confidence))

    sb = get_supabase_admin()
    result = (
        sb.table("user_memory")
        .insert({
            "user_id": user_id,
            "type": memory_type,
            "label": label,
            "content": content,
            "confidence": confidence,
        })
        .execute()
    )

    logger.info(f"Memory stored: type={memory_type}, label={label}, user={user_id[:8]}...")
    return result.data[0] if result.data else {}


async def retrieve_memories(
    user_id: str,
    min_confidence: float = MIN_RETRIEVAL_CONFIDENCE,
    memory_type: str = None,
    limit: int = 10,
) -> list[dict]:
    """
    Retrieve active memories above the confidence threshold.
    Updates last_used timestamp for retrieved memories.

    Returns:
        List of memory dicts sorted by confidence (highest first)
    """
    sb = get_supabase_admin()
    query = (
        sb.table("user_memory")
        .select("id, type, label, content, confidence, last_used")
        .eq("user_id", user_id)
        .gte("confidence", min_confidence)
        .order("confidence", desc=True)
        .limit(limit)
    )

    if memory_type:
        query = query.eq("type", memory_type)

    result = query.execute()
    memories = result.data or []

    # Touch last_used for retrieved memories (fire-and-forget)
    if memories:
        now = datetime.now(timezone.utc).isoformat()
        memory_ids = [m["id"] for m in memories]
        try:
            sb.table("user_memory").update(
                {"last_used": now}
            ).in_("id", memory_ids).execute()
        except Exception as e:
            logger.warning(f"Failed to update last_used: {e}")

    return memories


async def decay_memories(user_id: str) -> int:
    """
    Apply confidence decay to memories that haven't been used recently.
    Called periodically (e.g., at the start of each decision request).

    WHY: Prevents stale memories from dominating. If a pattern hasn't been
    relevant in recent interactions, its influence should diminish.

    Returns:
        Number of memories decayed
    """
    sb = get_supabase_admin()

    # Fetch all memories above minimum threshold
    result = (
        sb.table("user_memory")
        .select("id, confidence")
        .eq("user_id", user_id)
        .gt("confidence", 0.0)
        .execute()
    )

    decayed_count = 0
    for memory in (result.data or []):
        new_confidence = round(max(0.0, memory["confidence"] - CONFIDENCE_DECAY_RATE), 3)
        if new_confidence != memory["confidence"]:
            sb.table("user_memory").update(
                {"confidence": new_confidence}
            ).eq("id", memory["id"]).execute()
            decayed_count += 1

    if decayed_count:
        logger.info(f"Decayed {decayed_count} memories for user {user_id[:8]}...")
    return decayed_count


def format_memory_context(memories: list[dict]) -> str:
    """
    Format retrieved memories into a text block for prompt injection.
    Used by the aggregator to personalize responses.

    Returns empty string if no memories — caller handles the fallback.
    """
    if not memories:
        return ""

    lines = ["[User Context from Memory]"]
    for m in memories:
        conf_pct = int(m["confidence"] * 100)
        lines.append(f"- [{m['type']}] {m['label']}: {m['content']} (confidence: {conf_pct}%)")
    return "\n".join(lines)
