"""
Conflict Resolution Engine — MindMate v3.

Merges agent outputs, debate critiques, brain weights, and confidence scores
into a final reasoning summary. Replaces the old aggregator for the v3 pipeline.

The resolution is a weighted synthesis — not a bland average.
The dominant agent's perspective shapes the core; others layer in proportionally.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from app.models.schemas import AgentOutput, BrainConfig, AgentName

logger = logging.getLogger(__name__)

_RESOLUTION_PROMPT = """You are synthesizing multiple agent perspectives into ONE unified response for a user.

Brain weights (importance of each perspective):
{weights}

Agent outputs:
{agent_summaries}

{debate_context}

SYNTHESIS RULES:
- The highest-weighted agent's perspective should DOMINATE the response
- Layer in other agents' insights proportionally to their weights
- If debate critiques exist, incorporate their strongest points
- Output ONE clear, cohesive perspective — not a list of viewpoints
- Keep the tone matching the dominant perspective
- DO NOT mention agents, weights, or the process
- DO NOT hedge with "on one hand... on the other hand"
- BE DECISIVE. Give ONE clear response.

Respond with ONLY a JSON object:
{{"reasoning": "<2-3 sentences of internal reasoning>", "response": "<the response to give the user, max 3 sentences>"}}"""


def _build_weight_string(config: BrainConfig) -> str:
    """Build a compact weight description for the prompt."""
    weights = _weight_map(config)
    # Only show non-zero weights
    active = {k: v for k, v in weights.items() if v > 0}
    return ", ".join(f"{k}: {v:.2f}" for k, v in sorted(active.items(), key=lambda x: -x[1]))


def _weight_map(config: BrainConfig) -> Dict[str, float]:
    return {
        "analytical": config.analytical,
        "emotional": config.emotional,
        "ethical": config.ethical,
        "values": config.values,
        "red_team": config.red_team,
    }


def _calc_influence(output: AgentOutput, config: BrainConfig) -> float:
    weights = _weight_map(config)
    return round(weights.get(output.agent.value, 0.0) * output.confidence, 3)


def _build_agent_summaries(outputs: List[AgentOutput], config: BrainConfig) -> str:
    """Compress agent outputs with weight and influence for the resolution prompt."""
    lines = []
    for o in outputs:
        influence = _calc_influence(o, config)
        lines.append(
            f"[{o.agent.value}] (weight: {_weight_map(config).get(o.agent.value, 0):.2f}, "
            f"conf: {o.confidence:.2f}, influence: {influence:.2f})\n  {o.response[:200]}"
        )
    return "\n".join(lines)


def _build_debate_context(critiques: List[Dict[str, Any]], synthesis_suggestion: str) -> str:
    """Build debate context section if critiques exist."""
    if not critiques:
        return ""

    lines = ["Debate critiques:"]
    for c in critiques[:4]:  # Limit to 4 critiques for token efficiency
        lines.append(f"  - About {c.get('target_agent', '?')}: {c.get('critique', '')[:100]}")

    if synthesis_suggestion:
        lines.append(f"\nModeration suggestion: {synthesis_suggestion[:150]}")

    return "\n".join(lines)


def resolve_conflict(
    outputs: List[AgentOutput],
    brain_config: BrainConfig,
    call_groq_fn,
    critiques: Optional[List[Dict[str, Any]]] = None,
    synthesis_suggestion: str = "",
) -> Dict[str, str]:
    """
    Merge all agent perspectives into a final resolved response.

    Args:
        outputs: Agent reasoning outputs
        brain_config: User's brain weight configuration
        call_groq_fn: Groq API caller
        critiques: Optional debate critiques
        synthesis_suggestion: Optional synthesis hint from debate

    Returns:
        {"reasoning": str, "response": str}
    """
    if not outputs:
        return {
            "reasoning": "No agent outputs to resolve",
            "response": "I don't have enough context to give you a good answer. Could you tell me more?",
        }

    weights_str = _build_weight_string(brain_config)
    summaries_str = _build_agent_summaries(outputs, brain_config)
    debate_ctx = _build_debate_context(critiques or [], synthesis_suggestion)

    prompt = _RESOLUTION_PROMPT.format(
        weights=weights_str,
        agent_summaries=summaries_str,
        debate_context=debate_ctx,
    )

    try:
        raw = call_groq_fn(
            system_prompt=prompt,
            user_message="Synthesize the above into a single response.",
            temperature=0.6,
            max_tokens=250,
        )

        parsed = json.loads(raw.strip())
        return {
            "reasoning": parsed.get("reasoning", "Synthesis complete."),
            "response": parsed.get("response", raw[:300]),
        }

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Resolution JSON parse failed: {e}, using raw output")
        return {
            "reasoning": "Synthesis completed with fallback extraction.",
            "response": raw[:300] if 'raw' in dir() else "I need a moment. Could you rephrase that?",
        }
    except Exception as e:
        logger.error(f"Conflict resolution failed: {e}")
        return {
            "reasoning": f"Resolution error: {str(e)[:100]}",
            "response": "I'm having trouble thinking through this. Can you try asking again?",
        }
