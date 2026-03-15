"""
Three-Layer Memory Service — MindMate v3.

Implements the memory hierarchy:
  1. Short-term: Last 10 messages (conversation-scoped)
  2. Episodic: Top 5 vector-similar memories (user-scoped, pgvector)
  3. Semantic profile: User's persistent attributes (goals, people, preferences)

All memory retrieval produces a combined context string for prompt injection.
Token-aware truncation prevents context from exceeding budget.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

from db import get_supabase_admin

logger = logging.getLogger(__name__)

# Token budget for memory context (rough estimate: 1 token ≈ 4 chars)
MAX_CONTEXT_CHARS = 2000  # ~500 tokens
MAX_SHORT_TERM_MESSAGES = 10
MAX_EPISODIC_RESULTS = 5


# ========================= CONVERSATION MANAGEMENT =========================

async def create_conversation_record(
    conversation_id: str,
    user_id: str,
    title: str,
    brain_config: dict,
    tone_config: str,
) -> dict:
    """Create or update a conversational thread in the DB."""
    sb = get_supabase_admin()
    try:
        result = (
            sb.table("conversations")
            .upsert(
                {
                    "id": conversation_id,
                    "user_id": user_id,
                    "title": title,
                    "brain_config": brain_config,
                    "tone_config": tone_config,
                },
                on_conflict="id",
            )
            .execute()
        )
        return result.data[0] if result.data else {}
    except Exception as e:
        logger.warning(f"Failed to upsert conversation record: {e}")
        return {}


async def get_conversation_metadata(conversation_id: str) -> dict:
    """Fetch conversation metadata (title, user_id, configs)."""
    sb = get_supabase_admin()
    try:
        result = (
            sb.table("conversations")
            .select("id, user_id, title, brain_config, tone_config")
            .eq("id", conversation_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else {}
    except Exception as e:
        logger.warning(f"Failed to fetch conversation metadata: {e}")
        return {}


async def update_conversation_title(conversation_id: str, user_id: str, title: str) -> None:
    """Set conversation title and bump updated_at."""
    sb = get_supabase_admin()
    try:
        sb.table("conversations").update({
            "title": title,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", conversation_id).eq("user_id", user_id).execute()
    except Exception as e:
        logger.warning(f"Failed to update conversation title: {e}")


async def update_conversation_configs(
    conversation_id: str,
    user_id: str,
    brain_config: Optional[dict] = None,
    tone_config: Optional[str] = None,
) -> None:
    """Upsert brain/tone config for a conversation, scoped by owner."""
    if brain_config is None and tone_config is None:
        return

    sb = get_supabase_admin()
    payload = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if brain_config is not None:
        payload["brain_config"] = brain_config
    if tone_config is not None:
        payload["tone_config"] = tone_config

    try:
        sb.table("conversations").upsert(
            {
                "id": conversation_id,
                "user_id": user_id,
                **payload,
            },
            on_conflict="id",
        ).execute()
    except Exception as e:
        logger.warning(f"Failed to update conversation configs: {e}")


async def touch_conversation(
    conversation_id: str,
    user_id: str,
    brain_config: Optional[dict] = None,
    tone_config: Optional[str] = None,
) -> None:
    """Update conversation metadata on new activity."""
    sb = get_supabase_admin()
    payload = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if brain_config is not None:
        payload["brain_config"] = brain_config
    if tone_config is not None:
        payload["tone_config"] = tone_config

    try:
        sb.table("conversations").update(payload).eq("id", conversation_id).eq("user_id", user_id).execute()
    except Exception as e:
        logger.warning(f"Failed to touch conversation: {e}")


# ========================= SHORT-TERM MEMORY =========================

async def store_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
) -> dict:
    """Store a message in short-term memory."""
    sb = get_supabase_admin()
    result = (
        sb.table("messages")
        .insert({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
        })
        .execute()
    )
    return result.data[0] if result.data else {}


async def get_short_term_context(
    conversation_id: str,
    limit: int = MAX_SHORT_TERM_MESSAGES,
) -> str:
    """
    Retrieve last N messages for the conversation.
    Returns formatted string for prompt injection.
    """
    sb = get_supabase_admin()
    result = (
        sb.table("messages")
        .select("role, content, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    messages = result.data or []
    if not messages:
        return ""

    # Reverse to chronological order
    messages.reverse()

    lines = ["[Recent Conversation]"]
    for msg in messages:
        role_label = "User" if msg["role"] == "user" else "AI"
        # Truncate long messages in context
        content = msg["content"][:200]
        lines.append(f"{role_label}: {content}")

    return "\n".join(lines)


async def get_conversation_depth(conversation_id: str) -> int:
    """Count messages in a conversation (for complexity classification)."""
    sb = get_supabase_admin()
    result = (
        sb.table("messages")
        .select("id", count="exact")
        .eq("conversation_id", conversation_id)
        .execute()
    )
    return result.count or 0


# ========================= EPISODIC MEMORY (VECTOR) =========================

async def store_episodic_memory(
    user_id: str,
    content: str,
    embedding: List[float],
    importance_score: float = 0.5,
) -> dict:
    """Store an episodic memory with its embedding vector."""
    sb = get_supabase_admin()
    result = (
        sb.table("episodic_memory")
        .insert({
            "user_id": user_id,
            "content": content,
            "embedding": embedding,
            "importance_score": importance_score,
        })
        .execute()
    )
    return result.data[0] if result.data else {}


async def search_episodic_memories(
    user_id: str,
    query_embedding: List[float],
    limit: int = MAX_EPISODIC_RESULTS,
    threshold: float = 0.7,
) -> List[dict]:
    """
    Search episodic memories by vector similarity.
    Uses the match_episodic_memories Postgres function.
    """
    sb = get_supabase_admin()
    try:
        result = sb.rpc(
            "match_episodic_memories",
            {
                "query_embedding": query_embedding,
                "match_user_id": user_id,
                "match_count": limit,
                "match_threshold": threshold,
            }
        ).execute()
        return result.data or []
    except Exception as e:
        logger.warning(f"Episodic memory search failed: {e}")
        return []


def format_episodic_context(memories: List[dict]) -> str:
    """Format episodic memories into a context string."""
    if not memories:
        return ""

    lines = ["[Relevant Past Context]"]
    for mem in memories:
        score = int(mem.get("importance_score", 0.5) * 100)
        sim = int(mem.get("similarity", 0) * 100)
        lines.append(f"- {mem['content']} (relevance: {sim}%, importance: {score}%)")

    return "\n".join(lines)


# ========================= SEMANTIC USER PROFILE =========================

async def get_user_profile(user_id: str) -> dict:
    """Retrieve the user's semantic profile."""
    sb = get_supabase_admin()
    result = (
        sb.table("user_profile")
        .select("important_people, goals, preferences, recurring_issues")
        .eq("user_id", user_id)
        .execute()
    )

    if result.data:
        return result.data[0]

    # No profile yet — return empty structure
    return {
        "important_people": [],
        "goals": [],
        "preferences": {},
        "recurring_issues": [],
    }


async def update_user_profile(user_id: str, updates: dict) -> dict:
    """Upsert user profile fields."""
    sb = get_supabase_admin()
    payload = {"user_id": user_id, **updates, "updated_at": datetime.now(timezone.utc).isoformat()}
    result = (
        sb.table("user_profile")
        .upsert(payload, on_conflict="user_id")
        .execute()
    )
    return result.data[0] if result.data else {}


def format_profile_context(profile: dict) -> str:
    """Format user profile into a context string for prompt injection."""
    parts = []

    people = profile.get("important_people", [])
    if people:
        parts.append(f"Important people: {', '.join(people[:5])}")

    goals = profile.get("goals", [])
    if goals:
        parts.append(f"Goals: {', '.join(goals[:5])}")

    prefs = profile.get("preferences", {})
    if prefs:
        pref_items = [f"{k}: {v}" for k, v in list(prefs.items())[:5]]
        parts.append(f"Preferences: {', '.join(pref_items)}")

    issues = profile.get("recurring_issues", [])
    if issues:
        parts.append(f"Recurring themes: {', '.join(issues[:5])}")

    if not parts:
        return ""

    return "[User Profile]\n" + "\n".join(f"- {p}" for p in parts)


# ========================= COMBINED CONTEXT BUILDER =========================

async def build_memory_context(
    conversation_id: str,
    user_id: str,
    query_embedding: Optional[List[float]] = None,
) -> Dict[str, str]:
    """
    Build the complete memory context from all three layers.
    Returns dict with separate context strings for each layer.

    Token-aware: truncates combined context to MAX_CONTEXT_CHARS.
    """
    # Layer 1: Short-term
    short_term = await get_short_term_context(conversation_id)

    # Layer 2: Episodic (requires embedding)
    episodic = ""
    if query_embedding:
        memories = await search_episodic_memories(user_id, query_embedding)
        episodic = format_episodic_context(memories)

    # Layer 3: User profile
    profile = await get_user_profile(user_id)
    profile_ctx = format_profile_context(profile)

    # Token-aware truncation
    combined_length = len(short_term) + len(episodic) + len(profile_ctx)
    if combined_length > MAX_CONTEXT_CHARS:
        # Prioritize: profile > episodic > short-term (trim short-term first)
        budget = MAX_CONTEXT_CHARS
        profile_ctx = profile_ctx[:min(len(profile_ctx), budget // 3)]
        episodic = episodic[:min(len(episodic), budget // 3)]
        remaining = budget - len(profile_ctx) - len(episodic)
        short_term = short_term[:max(0, remaining)]

    return {
        "short_term": short_term,
        "episodic": episodic,
        "user_profile": profile_ctx,
    }
