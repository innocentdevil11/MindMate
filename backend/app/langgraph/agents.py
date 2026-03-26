"""
Agent Node Wrappers — MindMate v3 LangGraph.

Wraps existing agent implementations into LangGraph-compatible nodes
that return structured AgentOutput objects.

Key changes from v2:
  - Agents return structured {agent, reasoning, response, confidence} instead of raw text
  - Agents with weight=0 are skipped entirely (no API call)
  - Max tokens reduced from 1024 to 300 for token efficiency
  - Confidence is extracted from LLM output via JSON parsing
"""

import json
import logging
import concurrent.futures
from typing import Dict, Any, Optional

from agents.groq_client import call_groq
from app.models.schemas import AgentOutput, AgentName

logger = logging.getLogger(__name__)

# ========================= CONCISE AGENT PROMPTS =========================
# These replace the original verbose prompts for the v3 pipeline.
# Original prompts are preserved in the original agent files for backward compat.

_AGENT_PROMPTS = {
    "risk": {
        "system": (
            "You are the ANALYTICAL mind. Think with pure logic, strategy, and pragmatism. "
            "Evaluate outcomes, probabilities, and practical consequences. No emotion.\n\n"
            "Respond ONLY with JSON: "
            '{{"reasoning": "<2-3 sentences of analytical thought>", '
            '"response": "<1-2 sentences: your recommendation>", '
            '"confidence": <0.0-1.0>}}'
        ),
        "temperature": 0.3,
    },
    "eq": {
        "system": (
            "You are the EMOTIONAL mind. Think through feelings, relationships, and human connection. "
            "Consider how this affects loved ones. Feel deeply.\n\n"
            "Respond ONLY with JSON: "
            '{{"reasoning": "<2-3 sentences of emotional thought>", '
            '"response": "<1-2 sentences: your heart-driven perspective>", '
            '"confidence": <0.0-1.0>}}'
        ),
        "temperature": 0.7,
    },
    "ethical": {
        "system": (
            "You are the ETHICAL mind. Think through moral principles, duty, and dharmic wisdom. "
            "What is the right action? What does duty demand?\n\n"
            "Respond ONLY with JSON: "
            '{{"reasoning": "<2-3 sentences of moral reasoning>", '
            '"response": "<1-2 sentences: the ethical path>", '
            '"confidence": <0.0-1.0>}}'
        ),
        "temperature": 0.4,
    },
    "values": {
        "system": (
            "You are the VALUES mind. Think about identity, legacy, and who the person becomes. "
            "What does this choice say about their character?\n\n"
            "Respond ONLY with JSON: "
            '{{"reasoning": "<2-3 sentences of identity reflection>", '
            '"response": "<1-2 sentences: the values perspective>", '
            '"confidence": <0.0-1.0>}}'
        ),
        "temperature": 0.5,
    },
    "red_team": {
        "system": (
            "You are the RED TEAM mind — the skeptic, the devil's advocate. "
            "Challenge assumptions. What could go wrong? What's being overlooked?\n\n"
            "Respond ONLY with JSON: "
            '{{"reasoning": "<2-3 sentences of critical challenge>", '
            '"response": "<1-2 sentences: the uncomfortable truth>", '
            '"confidence": <0.0-1.0>}}'
        ),
        "temperature": 0.8,
    },
}

# Internal agent name → user-facing AgentName enum
_INTERNAL_TO_EXTERNAL = {
    "risk": AgentName.ANALYTICAL,
    "eq": AgentName.EMOTIONAL,
    "ethical": AgentName.ETHICAL,
    "values": AgentName.VALUES,
    "red_team": AgentName.RED_TEAM,
}

# Token limit for individual agent calls
AGENT_MAX_TOKENS = 200


def run_agent(
    agent_key: str,
    query: str,
    memory_context: str = "",
    intent: str = "",
) -> Optional[AgentOutput]:
    """
    Run a single cognitive agent and return structured output.

    Args:
        agent_key: Internal agent name ('risk', 'eq', 'ethical', 'values', 'red_team')
        query: The user's query
        memory_context: Optional memory context to inject

    Returns:
        AgentOutput or None if the agent fails
    """
    prompt_config = _AGENT_PROMPTS.get(agent_key)
    if not prompt_config:
        logger.error(f"Unknown agent key: {agent_key}")
        return None

    # Build user message with optional memory context
    user_msg = query
    if memory_context:
        user_msg = f"{memory_context}\n\nUser question: {query}"

    # Build system prompt with intent-specific constraints
    system = prompt_config["system"]
    if intent == "deep_problem":
        system += (
            "\n\nDilemma Guidelines (follow this 4-step structure BEFORE responding):\n"
            "1) Identify the core conflict and competing priorities.\n"
            "2) List 2-3 concrete options the user could take.\n"
            "3) Evaluate tradeoffs/risks for each option (1 sentence each).\n"
            "4) Recommend one balanced action and why.\n"
            "Keep the final response concise and actionable."
        )

    try:
        raw = call_groq(
            system_prompt=system,
            user_message=user_msg,
            temperature=prompt_config["temperature"],
            max_tokens=AGENT_MAX_TOKENS,
        )

        return _parse_agent_output(agent_key, raw)

    except Exception as e:
        logger.error(f"Agent '{agent_key}' failed: {e}")
        # Return a low-confidence fallback instead of crashing
        return AgentOutput(
            agent=_INTERNAL_TO_EXTERNAL[agent_key],
            reasoning=f"Agent error: {str(e)[:100]}",
            response="Unable to provide perspective at this time.",
            confidence=0.1,
        )


def _parse_agent_output(agent_key: str, raw: str) -> AgentOutput:
    """Parse structured JSON output from an agent. Fallback to raw text extraction."""
    agent_name = _INTERNAL_TO_EXTERNAL[agent_key]

    try:
        # Try JSON parsing first
        parsed = json.loads(raw.strip())
        return AgentOutput(
            agent=agent_name,
            reasoning=parsed.get("reasoning", "")[:500],
            response=parsed.get("response", "")[:300],
            confidence=float(parsed.get("confidence", 0.5)),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        # Fallback: treat entire output as response
        logger.debug(f"Agent '{agent_key}' returned non-JSON output, using fallback parser")
        # Try to extract from malformed JSON
        response = raw[:300].strip()
        return AgentOutput(
            agent=agent_name,
            reasoning="Extracted from unstructured output.",
            response=response,
            confidence=0.5,
        )


def run_all_active_agents(
    query: str,
    weights: Dict[str, float],
    memory_context: str = "",
    intent: str = "",
) -> list[AgentOutput]:
    """
    Run all agents with weight > 0 in parallel.

    Args:
        query: User query
        weights: Internal weights dict {'risk': 0.3, 'eq': 0.2, ...}
        memory_context: Combined memory context string

    Returns:
        List of AgentOutput from active agents
    """
    active_agents = [(k, w) for k, w in weights.items() if w > 0]

    if not active_agents:
        return []

    outputs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(active_agents)) as executor:
        futures = {
            executor.submit(run_agent, agent_key, query, memory_context, intent): agent_key
            for agent_key, _ in active_agents
        }
        for future in concurrent.futures.as_completed(futures):
            agent_key = futures[future]
            try:
                result = future.result(timeout=10)
                if result:
                    outputs.append(result)
            except Exception as e:
                logger.error(f"Agent '{agent_key}' parallel execution failed: {e}")

    return outputs
