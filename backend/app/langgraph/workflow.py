"""
MindMate v3 — LangGraph Cognitive Pipeline.

This is the central reasoning workflow. It replaces the old flat
fan-out/fan-in graph with a conditional pipeline:

  START → intent → complexity → route
    ├── SIMPLE:  direct response → personality → length control → END
    ├── MEDIUM:  agents → conflict resolution → personality → length control → END
    └── COMPLEX: agents → debate → conflict resolution → personality → length control → END

Each node operates on a shared state dict and appends thinking trace steps.
"""

import json
import logging
import uuid
from typing import Dict, Any, Annotated
from operator import add

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from agents.groq_client import call_groq
from app.models.schemas import (
    Intent, Complexity, AgentName, BrainConfig,
    AgentOutput, ThinkingTrace, StepType, TraceStep,
    IntentResult, ComplexityResult,
)
from app.services.intent_classifier import classify_intent
from app.services.complexity_classifier import classify_complexity
from app.services.personality_engine import get_personality_tone
from app.services.response_controller import control_response, extract_recent_assistant_responses
from app.services.brain_engine import normalize_weights, get_active_agents, get_dominant_agents
from app.services.debate_engine import run_debate, compute_disagreement_score, DEBATE_THRESHOLD
from app.services.conflict_resolution import resolve_conflict
from app.services.conversation_mode import detect_mode_override, CASUAL_CHAT_SYSTEM_RULES
from app.langgraph.agents import run_all_active_agents
from app.langgraph.orchestrator import (
    route_by_complexity,
    should_debate,
    select_debate_agents,
    weighted_agent_order,
)

logger = logging.getLogger(__name__)


# ========================= GRAPH STATE =========================
# Using TypedDict for LangGraph compatibility (Pydantic models need extra config)

class MindMateState(TypedDict):
    """State flowing through the LangGraph pipeline."""
    # Input
    user_query: str
    conversation_id: str
    message_id: str
    user_id: str

    # Brain config (as dict for LangGraph serialization)
    brain_config: Dict[str, float]

    # Memory context
    memory_context: str

    # Classification results
    intent: str          # Intent enum value
    complexity: str      # Complexity enum value
    conversation_depth: int

    # Agent outputs (list of dicts)
    agent_outputs: list

    # Debate results
    critiques: list
    disagreement_score: float
    synthesis_suggestion: str

    # Resolution
    resolved_reasoning: str
    resolved_response: str

    # Personality & final
    tone_instruction: str
    final_response: str

    # Conversation mode override
    conversation_mode: str

    # Thinking trace (list of step dicts)
    trace_steps: list


# ========================= NODE FUNCTIONS =========================

def intent_node(state: MindMateState) -> dict:
    """Classify user intent."""
    result = classify_intent(state["user_query"], call_groq)

    trace_step = {
        "step_type": StepType.INTENT.value,
        "agent": None,
        "content": f"Intent: {result.intent.value} (confidence: {result.confidence:.2f})",
    }

    return {
        "intent": result.intent.value,
        "trace_steps": [trace_step],
    }


def mode_override_node(state: MindMateState) -> dict:
    """Detect user-requested conversation mode overrides (e.g. 'just talk to me')."""
    current_mode = state.get("conversation_mode", "normal")
    new_mode = detect_mode_override(state["user_query"], current_mode)

    trace_step = {
        "step_type": StepType.INTENT.value,
        "agent": None,
        "content": f"Conversation mode: {current_mode} → {new_mode}",
    }

    result = {"conversation_mode": new_mode, "trace_steps": [trace_step]}

    # If switching to casual_chat, force simple complexity to skip agents
    if new_mode == "casual_chat":
        logger.info("Casual chat mode active — forcing simple complexity, disabling agents")
        result["complexity"] = "simple"

    return result


def complexity_node(state: MindMateState) -> dict:
    """Classify query complexity."""
    # If mode_override already forced complexity, skip classification
    if state.get("conversation_mode") == "casual_chat":
        trace_step = {
            "step_type": StepType.COMPLEXITY.value,
            "agent": None,
            "content": "Complexity: simple (forced by casual_chat mode)",
        }
        return {
            "complexity": "simple",
            "trace_steps": [trace_step],
        }

    intent = Intent(state["intent"])
    depth = state.get("conversation_depth", 0)

    result = classify_complexity(state["user_query"], intent, depth)

    trace_step = {
        "step_type": StepType.COMPLEXITY.value,
        "agent": None,
        "content": f"Complexity: {result.complexity.value} — {result.reasoning}",
    }

    return {
        "complexity": result.complexity.value,
        "trace_steps": [trace_step],
    }


def simple_response_node(state: MindMateState) -> dict:
    """Generate a direct response for simple queries (no agents)."""
    intent = Intent(state["intent"])
    brain_config = BrainConfig(**state["brain_config"])
    user_tone = state.get("tone_instruction", "clean")
    conversation_mode = state.get("conversation_mode", "normal")

    # Use the user's selected tone — always respect their preference
    tone = get_personality_tone(brain_config, user_tone)

    # ── CASUAL CHAT MODE: strict friend-mode prompt ──
    if conversation_mode == "casual_chat":
        system_prompt = (
            f"You are MindMate, a chill AI companion. "
            f"{tone}\n"
            f"{CASUAL_CHAT_SYSTEM_RULES}"
        )
        logger.info("simple_response_node: using casual_chat prompt (agents disabled)")
    else:
        # Standard simple response prompt
        system_prompt = (
            f"You are MindMate, a thoughtful AI companion. "
            f"{tone}\n"
            "RULES FOR GREETINGS AND CASUAL CHAT:\n"
            "- When responding to greetings, speak casually like a human in chat.\n"
            "- Keep it short (1-2 sentences).\n"
            "- Do not introduce yourself formally unless asked.\n"
            "- Avoid phrases like: 'Welcome to our conversation', 'I am here to assist you', 'How may I assist you today'.\n"
            "- Avoid repeating identical greeting patterns across conversations.\n"
            "- CRITICAL RULE: DO NOT repeat back what the user just said or your own previous responses."
        )

    memory = state.get("memory_context", "")
    user_msg = state["user_query"]
    if memory:
        user_msg = f"{memory}\n\nUser: {user_msg}"

    response = call_groq(
        system_prompt=system_prompt,
        user_message=user_msg,
        temperature=0.7,
        max_tokens=100,
    )

    recent_ai = extract_recent_assistant_responses(state.get("memory_context", ""))
    processed = control_response(
        response,
        state["user_query"],
        previous_responses=recent_ai,
    )

    trace_step = {
        "step_type": StepType.FINAL_OUTPUT.value,
        "agent": None,
        "content": f"Simple path response (intent={intent.value}, mode={conversation_mode})",
    }

    return {
        "final_response": processed,
        "resolved_reasoning": f"Simple/casual path — mode={conversation_mode}, no agent reasoning.",
        "resolved_response": processed,
        "trace_steps": [trace_step],
    }


def agent_reasoning_node(state: MindMateState) -> dict:
    """Run all active cognitive agents in parallel."""
    brain_config = BrainConfig(**state["brain_config"])
    memory_context = state.get("memory_context", "")

    normalized = normalize_weights(brain_config.model_dump())
    active = get_active_agents(normalized)
    dominant = get_dominant_agents(active, k=2)

    logger.info(f"Active agents: {active}")
    logger.info(f"Dominant agents: {dominant}")

    internal_weights = {
        "risk": dominant.get("analytical", 0.0),
        "eq": dominant.get("emotional", 0.0),
        "ethical": dominant.get("ethical", 0.0),
        "values": dominant.get("values", 0.0),
        "red_team": dominant.get("red_team", 0.0),
    }

    outputs = run_all_active_agents(
        query=state["user_query"],
        weights=internal_weights,
        memory_context=memory_context,
        intent=state.get("intent", ""),
    )

    # Convert to dicts for LangGraph state
    output_dicts = [o.model_dump() for o in outputs]

    trace_steps = []
    for o in outputs:
        trace_steps.append({
            "step_type": StepType.AGENT_REASONING.value,
            "agent": o.agent.value,
            "content": f"[{o.agent.value}] (conf={o.confidence:.2f}) {o.response[:150]}",
        })

    return {
        "agent_outputs": output_dicts,
        "trace_steps": trace_steps,
    }


def debate_gate_node(state: MindMateState) -> dict:
    """
    Conditional gate: decides whether to run debate.
    Always runs — the routing happens via conditional edges after this.
    """
    complexity = Complexity(state["complexity"])
    outputs = [AgentOutput(**o) for o in state.get("agent_outputs", [])]
    brain_config = BrainConfig(**state["brain_config"])
    dominant = select_debate_agents(outputs, brain_config, k=2)
    disagreement = compute_disagreement_score(dominant or outputs)

    return {
        "disagreement_score": disagreement,
    }


def debate_node(state: MindMateState) -> dict:
    """Run the adaptive debate process."""
    outputs = [AgentOutput(**o) for o in state.get("agent_outputs", [])]
    brain_config = BrainConfig(**state["brain_config"])

    debate_inputs = select_debate_agents(outputs, brain_config, k=2) or outputs

    debate_result = run_debate(
        outputs=debate_inputs,
        user_query=state["user_query"],
        call_groq_fn=call_groq,
        intent=state.get("intent", ""),
    )

    trace_steps = []
    for critique in debate_result.get("critiques", []):
        trace_steps.append({
            "step_type": StepType.DEBATE_CRITIQUE.value,
            "agent": critique.get("target_agent"),
            "content": f"Critique of {critique.get('target_agent', '?')}: {critique.get('critique', '')[:150]}",
        })

    return {
        "critiques": debate_result.get("critiques", []),
        "synthesis_suggestion": debate_result.get("synthesis_suggestion", ""),
        "disagreement_score": debate_result.get("disagreement_score", 0),
        "trace_steps": trace_steps,
    }


def conflict_resolution_node(state: MindMateState) -> dict:
    """Merge agent outputs into a single resolved response."""
    outputs = [AgentOutput(**o) for o in state.get("agent_outputs", [])]
    brain_config = BrainConfig(**state["brain_config"])
    critiques = state.get("critiques", [])
    synthesis = state.get("synthesis_suggestion", "")

    # Order by influence so brain weights meaningfully steer synthesis
    ordered_outputs = weighted_agent_order(outputs, brain_config)

    result = resolve_conflict(
        outputs=ordered_outputs,
        brain_config=brain_config,
        call_groq_fn=call_groq,
        critiques=critiques,
        synthesis_suggestion=synthesis,
    )

    trace_step = {
        "step_type": StepType.CONFLICT_RESOLUTION.value,
        "agent": None,
        "content": f"Resolution: {result['reasoning'][:200]}",
    }

    return {
        "resolved_reasoning": result["reasoning"],
        "resolved_response": result["response"],
        "trace_steps": [trace_step],
    }


def personality_node(state: MindMateState) -> dict:
    """Apply personality styling to the resolved response."""
    brain_config = BrainConfig(**state["brain_config"])
    user_tone = state.get("tone_instruction", "clean")
    tone = get_personality_tone(brain_config, user_tone)
    response = state.get("resolved_response", "")

    # Apply tone via a lightweight LLM pass with strict anti-repetition
    system_prompt = (
        f"{tone}\n\n"
        "Rephrase the following response to match the personality above. "
        "Keep the core message identical. Only adjust tone and word choice. "
        "Max 3 sentences. Do NOT add new information.\n"
        "CRITICAL RULES:\n"
        "- DO NOT repeat phrasing from previous messages in the context. Make it sound fresh and natural.\n"
        "- Only ask a follow-up question if it helps the user explore the topic further.\n"
        "- Avoid asking a question by default (skip follow-ups for factual questions or if the answer is complete).\n"
        "- Do not repeat similar follow-up phrasing across messages."
    )

    styled = call_groq(
        system_prompt=system_prompt,
        user_message=response,
        temperature=0.6,
        max_tokens=150,
    )

    trace_step = {
        "step_type": StepType.PERSONALITY_STYLING.value,
        "agent": None,
        "content": f"Applied tone: {tone[:80]}...",
    }

    return {
        "tone_instruction": tone,
        "resolved_response": styled,
        "trace_steps": [trace_step],
    }


def response_control_node(state: MindMateState) -> dict:
    """Enforce response length and add follow-up questions."""
    response = state.get("resolved_response", "")
    query = state.get("user_query", "")
    recent_ai = extract_recent_assistant_responses(state.get("memory_context", ""))

    controlled = control_response(
        response,
        query,
        previous_responses=recent_ai,
    )

    trace_step = {
        "step_type": StepType.RESPONSE_CONTROL.value,
        "agent": None,
        "content": f"Length controlled: {len(controlled)} chars",
    }

    return {
        "final_response": controlled,
        "trace_steps": [trace_step],
    }


# ========================= ROUTING FUNCTIONS =========================

def _route_complexity(state: MindMateState) -> str:
    """Conditional edge: route based on complexity classification."""
    complexity = Complexity(state["complexity"])
    return route_by_complexity(complexity)


def _route_debate(state: MindMateState) -> str:
    """Conditional edge: decide whether to debate or skip to resolution."""
    complexity = Complexity(state["complexity"])
    disagreement = state.get("disagreement_score", 0.0)
    intent_value = state.get("intent", "")

    if intent_value == Intent.DEEP_PROBLEM.value and disagreement > DEBATE_THRESHOLD:
        return "debate"

    if should_debate(complexity, disagreement):
        return "debate"
    return "conflict_resolution"


# ========================= STATE REDUCER =========================

def _merge_trace_steps(left: list, right: list) -> list:
    """Reducer: append trace steps from each node."""
    return (left or []) + (right or [])


def _replace(left, right):
    """Reducer: last write wins for scalar fields."""
    return right if right is not None else left


def _replace_list(left: list, right: list) -> list:
    """Reducer for list fields that should be replaced, not appended."""
    return right if right else left


# ========================= GRAPH BUILDER =========================

# State with reducers for parallel-safe updates
class MindMateStateWithReducers(TypedDict):
    user_query: str
    conversation_id: str
    message_id: str
    user_id: str
    brain_config: Dict[str, float]
    memory_context: str
    intent: str
    complexity: str
    conversation_depth: int
    agent_outputs: list
    critiques: list
    disagreement_score: float
    synthesis_suggestion: str
    resolved_reasoning: str
    resolved_response: str
    tone_instruction: str
    final_response: str
    conversation_mode: str
    trace_steps: Annotated[list, _merge_trace_steps]


def build_mindmate_v3_graph():
    """
    Build the MindMate v3 conditional reasoning pipeline.

    Graph structure:
      START → intent → complexity → [route]
        ├── simple_response → END
        └── agent_reasoning → debate_gate → [route]
              ├── debate → conflict_resolution → personality → response_control → END
              └── conflict_resolution → personality → response_control → END
    """
    graph = StateGraph(MindMateStateWithReducers)

    # Register nodes
    graph.add_node("intent", intent_node)
    graph.add_node("mode_override", mode_override_node)
    graph.add_node("complexity", complexity_node)
    graph.add_node("simple_response", simple_response_node)
    graph.add_node("agent_reasoning", agent_reasoning_node)
    graph.add_node("debate_gate", debate_gate_node)
    graph.add_node("debate", debate_node)
    graph.add_node("conflict_resolution", conflict_resolution_node)
    graph.add_node("personality", personality_node)
    graph.add_node("response_control", response_control_node)

    # Edges: linear start → intent → mode_override → complexity
    graph.add_edge(START, "intent")
    graph.add_edge("intent", "mode_override")
    graph.add_edge("mode_override", "complexity")

    # Conditional: route by complexity
    graph.add_conditional_edges(
        "complexity",
        _route_complexity,
        {
            "simple_response": "simple_response",
            "agent_reasoning": "agent_reasoning",
        },
    )

    # Simple path ends directly
    graph.add_edge("simple_response", END)

    # Agent reasoning → debate gate
    graph.add_edge("agent_reasoning", "debate_gate")

    # Conditional: debate or skip
    graph.add_conditional_edges(
        "debate_gate",
        _route_debate,
        {
            "debate": "debate",
            "conflict_resolution": "conflict_resolution",
        },
    )

    # Debate → conflict resolution
    graph.add_edge("debate", "conflict_resolution")

    # Conflict resolution → personality → response control → END
    graph.add_edge("conflict_resolution", "personality")
    graph.add_edge("personality", "response_control")
    graph.add_edge("response_control", END)

    return graph.compile()
