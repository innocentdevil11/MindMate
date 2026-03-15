"""
Orchestrator — MindMate v3 LangGraph.

Routing functions for conditional edges in the LangGraph workflow.
Determines which path a query takes through the reasoning pipeline.
"""

import logging
from typing import List

from app.models.schemas import Complexity, BrainConfig, AgentOutput
from app.services.debate_engine import DEBATE_THRESHOLD
from app.services.brain_engine import top_agents_by_influence, rank_outputs_by_influence

logger = logging.getLogger(__name__)


def route_by_complexity(complexity: Complexity) -> str:
    """
    Route to the appropriate processing path based on complexity.

    Returns:
        Node name to route to:
          "simple_response"  — direct LLM response, no agents
          "agent_reasoning"  — multi-agent, no debate
          "agent_reasoning"  — multi-agent + debate (debate is triggered conditionally later)
    """
    if complexity == Complexity.SIMPLE:
        return "simple_response"
    else:
        # Both MEDIUM and COMPLEX go through agent reasoning first.
        # COMPLEX will additionally trigger debate after agent outputs.
        return "agent_reasoning"


def should_debate(complexity: Complexity, disagreement_score: float = 0.0) -> bool:
    """
    Determine whether to run the debate phase.

    Debate only triggers when:
      1. Complexity is COMPLEX
      2. (OR) Disagreement score is above threshold even for MEDIUM

    This allows medium-complexity queries to "upgrade" to debate
    if agents substantially disagree.
    """
    if complexity == Complexity.COMPLEX:
        return True

    # Medium queries can trigger debate if agents disagree beyond threshold
    if complexity == Complexity.MEDIUM and disagreement_score > DEBATE_THRESHOLD:
        logger.info("Medium complexity upgraded to debate due to disagreement")
        return True

    return False


def weighted_agent_order(
    outputs: List[AgentOutput],
    brain_config: BrainConfig,
) -> List[AgentOutput]:
    """Order agent outputs by influence (weight * confidence)."""
    return rank_outputs_by_influence(outputs, brain_config)


def select_debate_agents(
    outputs: List[AgentOutput],
    brain_config: BrainConfig,
    k: int = 2,
) -> List[AgentOutput]:
    """
    Limit debate to the most influential agents so sliders have bite.
    Only the top-k agents (by weight * confidence) participate.
    """
    return top_agents_by_influence(outputs, brain_config, k=k)
