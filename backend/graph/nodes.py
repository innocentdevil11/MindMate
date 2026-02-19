from agents.ethical_agent_file import run_ethical_agent
from agents.eq_agent import run_eq_agent
from agents.risk_logic_agent import run_risk_agent
from agents.red_team_agent import run_red_team_agent
from agents.value_alignment_agent import run_values_agent
from agents.aggregator import run_aggregator_agent
from graph.state import SynapseState

# ---------- INDIVIDUAL AGENT NODES ----------
# NOTE: These remain unchanged — each agent processes the raw query.
# Personalization (tone, memory) is handled at the aggregator level,
# not at individual agent level, to avoid duplicating logic.

def ethical_node(state: SynapseState):
    output = run_ethical_agent(state["user_query"])
    return {
        "agent_outputs": {
            "ethical": {"output": output}
        }
    }

def eq_node(state: SynapseState):
    output = run_eq_agent(state["user_query"])
    return {
        "agent_outputs": {
            "eq": {"output": output}
        }
    }

def risk_node(state: SynapseState):
    output = run_risk_agent(state["user_query"])
    return {
        "agent_outputs": {
            "risk": {"output": output}
        }
    }

def red_team_node(state: SynapseState):
    output = run_red_team_agent(state["user_query"])
    return {
        "agent_outputs": {
            "red_team": {"output": output}
        }
    }

def values_node(state: SynapseState):
    output = run_values_agent(state["user_query"])
    return {
        "agent_outputs": {
            "values": {"output": output}
        }
    }

# ---------- FINAL AGGREGATOR NODE ----------
# Modified: now passes tone_preference and memory_context to the aggregator
def aggregator_node(state: SynapseState):
    payload = {
        "user_query": state["user_query"],
        "weights": state["weights"],
        "agent_outputs": state["agent_outputs"],
        # NEW: personalization context for tone-aware + memory-aware synthesis
        "tone_preference": state.get("tone_preference", "clean"),
        "memory_context": state.get("memory_context", ""),
    }
    final_answer = run_aggregator_agent(payload)

    # Build explanation metadata (Feature 5: Observability)
    memory_ctx = state.get("memory_context", "")
    explanation = {
        "tone_mode": state.get("tone_preference", "clean"),
        "memory_labels_used": _extract_memory_labels(memory_ctx),
        "has_memory_context": bool(memory_ctx),
        "response_confidence": _estimate_confidence(state),
    }

    return {
        "final_answer": final_answer,
        "agent_outputs": state["agent_outputs"],
        "explanation_metadata": explanation,
    }


def _extract_memory_labels(memory_context: str) -> list[str]:
    """Extract memory labels from the formatted context string."""
    labels = []
    for line in memory_context.split("\n"):
        # Format: "- [type] label: content (confidence: X%)"
        if line.startswith("- ["):
            try:
                after_bracket = line.split("] ", 1)[1]
                label = after_bracket.split(":")[0].strip()
                labels.append(label)
            except (IndexError, ValueError):
                continue
    return labels


def _estimate_confidence(state: SynapseState) -> float:
    """
    Estimate overall response confidence based on available context.

    WHY: Lets downstream consumers know how personalized/reliable
    the response is. Low confidence = generic fallback was used.
    """
    confidence = 0.5  # Base confidence for any LLM response

    # Having memory context increases confidence
    if state.get("memory_context"):
        confidence += 0.2

    # Having a non-default tone preference means user has customized
    if state.get("tone_preference") and state["tone_preference"] != "clean":
        confidence += 0.1

    # All agents produced output
    outputs = state.get("agent_outputs", {})
    if len(outputs) == 5:
        confidence += 0.2

    return min(1.0, round(confidence, 2))