"""
Brain Engine — MindMate v3.

Loads and manages brain configuration (agent weights) per conversation.
Falls back through: conversation config → evolved user defaults → system defaults.
"""

import logging
import uuid
from typing import Optional, List, Dict

from db import get_supabase_admin
from app.models.schemas import BrainConfig, AgentOutput, AgentName

logger = logging.getLogger(__name__)

# System-wide defaults
_DEFAULT_WEIGHTS = {
    "analytical": 0.25,
    "emotional": 0.25,
    "ethical": 0.25,
    "values": 0.25,
    "red_team": 0.0,
}


async def load_brain_config(
    conversation_id: str,
    user_id: str,
    override: Optional[BrainConfig] = None,
) -> BrainConfig:
    """
    Load brain configuration with fallback chain:
      1. Explicit override (from request)
      2. Stored per-conversation config
      3. User's evolved defaults (from brain evolution)
      4. System defaults

    Args:
        conversation_id: Current conversation UUID
        user_id: Authenticated user UUID
        override: Optional explicit weights from the request
    """
    # Priority 1: Explicit override
    if override:
        # Store the override as the conversation's config
        await save_brain_config(conversation_id, user_id, override)
        return override

    sb = get_supabase_admin()

    # Priority 2: Existing conversation config
    result = (
        sb.table("brain_config")
        .select("weights")
        .eq("conversation_id", conversation_id)
        .execute()
    )
    if result.data:
        weights = result.data[0]["weights"]
        return BrainConfig(**weights)

    # Priority 3: User's evolved defaults
    evolved = (
        sb.table("evolved_brain_defaults")
        .select("preferred_weights")
        .eq("user_id", user_id)
        .execute()
    )
    if evolved.data:
        weights = evolved.data[0]["preferred_weights"]
        config = BrainConfig(**weights)
        # Save as conversation config
        await save_brain_config(conversation_id, user_id, config)
        return config

    # Priority 4: System defaults
    config = BrainConfig(**_DEFAULT_WEIGHTS)
    await save_brain_config(conversation_id, user_id, config)
    return config


async def save_brain_config(
    conversation_id: str,
    user_id: str,
    config: BrainConfig,
) -> dict:
    """Store/update brain config for a conversation."""
    sb = get_supabase_admin()
    payload = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "weights": config.model_dump(),
    }
    result = (
        sb.table("brain_config")
        .upsert(payload, on_conflict="conversation_id")
        .execute()
    )
    logger.debug(f"Brain config saved for conversation {conversation_id[:8]}")
    return result.data[0] if result.data else {}


def create_conversation_id() -> str:
    """Generate a new conversation UUID."""
    return str(uuid.uuid4())


# ======== WEIGHTED AGENT HELPERS ========


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize a weight dict; fallback to analytical if all zero."""
    total = sum(weights.values()) if weights else 0.0
    if total <= 0:
        return {"analytical": 1.0}
    return {k: (v / total) for k, v in weights.items()}


def get_active_agents(weights: Dict[str, float], threshold: float = 0.05) -> Dict[str, float]:
    """Filter out agents below threshold to avoid phantom participation."""
    active = {k: v for k, v in weights.items() if v > threshold}
    return active or {"analytical": 1.0}


def get_dominant_agents(weights: Dict[str, float], k: int = 2) -> Dict[str, float]:
    """Return top-k agents by weight (already normalized/filtered)."""
    if k <= 0:
        return {}
    sorted_agents = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    top = dict(sorted_agents[:k])
    return top or {"analytical": 1.0}


def rank_outputs_by_influence(
    outputs: List[AgentOutput],
    brain_config: BrainConfig,
) -> List[AgentOutput]:
    """
    Sort agent outputs by influence (confidence * brain weight).

    Higher weighted influence = stronger contribution in synthesis.
    """
    weight_map = {
        AgentName.ANALYTICAL: brain_config.analytical,
        AgentName.EMOTIONAL: brain_config.emotional,
        AgentName.ETHICAL: brain_config.ethical,
        AgentName.VALUES: brain_config.values,
        AgentName.RED_TEAM: brain_config.red_team,
    }

    return sorted(
        outputs,
        key=lambda o: weight_map.get(o.agent, 0.0) * o.confidence,
        reverse=True,
    )


def top_agents_by_influence(
    outputs: List[AgentOutput],
    brain_config: BrainConfig,
    k: int = 2,
) -> List[AgentOutput]:
    """Return the top-k most influential agent outputs (weight * confidence)."""
    if k <= 0:
        return []

    ranked = rank_outputs_by_influence(outputs, brain_config)

    weight_map = {
        AgentName.ANALYTICAL: brain_config.analytical,
        AgentName.EMOTIONAL: brain_config.emotional,
        AgentName.ETHICAL: brain_config.ethical,
        AgentName.VALUES: brain_config.values,
        AgentName.RED_TEAM: brain_config.red_team,
    }

    # Ignore agents the user zeroed out
    filtered = [o for o in ranked if weight_map.get(o.agent, 0.0) > 0]
    return filtered[:k]
