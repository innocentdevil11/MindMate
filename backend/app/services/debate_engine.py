"""
Adaptive Debate Engine — MindMate v3.

Only activates for COMPLEX queries.
Implements a critique-based debate between agents.

Pipeline:
  Agent outputs → Critique round → Disagreement check → Optional 2nd round

Max 2 rounds. Token-efficient: uses compressed agent summaries for critiques.
"""

import json
import logging
from typing import List, Dict, Any

from app.models.schemas import AgentOutput, AgentName

logger = logging.getLogger(__name__)

# Disagreement threshold — above this triggers a second critique round
DISAGREEMENT_THRESHOLD = 0.3

# Minimum disagreement to trigger debate at all
DEBATE_THRESHOLD = 0.15

# Maximum debate rounds
MAX_DEBATE_ROUNDS = 2

# Compact critique prompt
_CRITIQUE_PROMPT = """You are a debate moderator reviewing agent outputs on a user's question.

Each agent gave a brief response. Identify:
1. Where agents DISAGREE on conclusions
2. Which agent's reasoning has gaps or unsupported claims
3. A 1-sentence synthesis suggestion

Be extremely concise. Max 3 sentences per critique.

Respond as JSON: {"critiques": [{"target_agent": "<name>", "critique": "<text>"}], "synthesis_suggestion": "<text>"}"""


def compute_disagreement_score(outputs: List[AgentOutput]) -> float:
    """
    Compute how much agents disagree.

    Factors:
      1. Confidence spread (high variance = more disagreement)
      2. Number of agents with low confidence (< 0.5)

    Returns score 0.0 (full agreement) to 1.0 (total conflict).
    """
    if len(outputs) <= 1:
        return 0.0

    confidences = [o.confidence for o in outputs]
    avg_confidence = sum(confidences) / len(confidences)

    # Variance-based disagreement
    variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)

    # Normalize: variance of 0.25 = full distance between 0 and 1
    normalized_variance = min(1.0, variance / 0.25)

    # Low-confidence penalty: if many agents are unsure, there's implicit disagreement
    low_confidence_ratio = sum(1 for c in confidences if c < 0.5) / len(confidences)

    # Weighted combination
    score = (normalized_variance * 0.6) + (low_confidence_ratio * 0.4)

    return round(min(1.0, score), 3)


def _compress_outputs_for_critique(outputs: List[AgentOutput]) -> str:
    """Compress agent outputs into a minimal string for the critique prompt."""
    lines = []
    for o in outputs:
        lines.append(f"[{o.agent.value}] (conf={o.confidence}): {o.response[:150]}")
    return "\n".join(lines)


def run_debate(
    outputs: List[AgentOutput],
    user_query: str,
    call_groq_fn,
    intent: str = "",
) -> Dict[str, Any]:
    """
    Run the adaptive debate process.

    Args:
        outputs: List of agent outputs from the parallel reasoning phase
        user_query: The user's original query
        call_groq_fn: Groq API caller (injected to avoid circular imports)
        intent: The classified user intent

    Returns:
        {
            "critiques": [...],
            "rounds_executed": int,
            "disagreement_score": float,
            "synthesis_suggestion": str,
        }
    """
    disagreement = compute_disagreement_score(outputs)
    logger.info(f"Debate disagreement score: {disagreement}")

    all_critiques = []
    synthesis_suggestion = ""
    rounds = 0

    # Only debate if there's meaningful disagreement
    # Force debate for deep problems if any disagreement exists among multiple agents
    force_debate = (intent == "deep_problem" and len(outputs) > 1 and disagreement > 0.0)

    if not force_debate and disagreement < DEBATE_THRESHOLD:
        logger.info(f"Low disagreement ({disagreement} < {DEBATE_THRESHOLD}) — skipping debate")
        return {
            "critiques": [],
            "rounds_executed": 0,
            "disagreement_score": disagreement,
            "synthesis_suggestion": "Agents largely agree. Proceed with weighted synthesis.",
        }

    # Run critique rounds
    for round_num in range(MAX_DEBATE_ROUNDS):
        compressed = _compress_outputs_for_critique(outputs)
        user_msg = f"Question: {user_query[:200]}\n\nAgent outputs:\n{compressed}"

        try:
            raw = call_groq_fn(
                system_prompt=_CRITIQUE_PROMPT,
                user_message=user_msg,
                temperature=0.3,
                max_tokens=200,
            )

            parsed = json.loads(raw.strip())
            critiques = parsed.get("critiques", [])
            synthesis_suggestion = parsed.get("synthesis_suggestion", "")

            all_critiques.extend(critiques)
            rounds += 1

            # Recompute disagreement after critique
            # If disagreement dropped below threshold, stop debating
            if round_num == 0 and disagreement <= DISAGREEMENT_THRESHOLD:
                logger.info("Disagreement below threshold after round 1 — stopping debate")
                break

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Debate round {round_num + 1} failed: {e}")
            break

    return {
        "critiques": all_critiques,
        "rounds_executed": rounds,
        "disagreement_score": disagreement,
        "synthesis_suggestion": synthesis_suggestion,
    }
