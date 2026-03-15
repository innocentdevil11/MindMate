"""
MindMate v3 — Pydantic schemas.

All request/response models, internal data structures, and enums
for the multi-agent cognition pipeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ========================= ENUMS =========================

class Intent(str, Enum):
    GREETING = "greeting"
    SMALLTALK = "smalltalk"
    EMOTIONAL_DISTRESS = "emotional_distress"
    FRUSTRATION = "frustration"
    FOLLOW_UP = "follow_up"
    DEEP_PROBLEM = "deep_problem"
    ADVICE_REQUEST = "advice_request"
    FACTUAL_QUESTION = "factual_question"
    REFLECTION = "reflection"
    GRATITUDE = "gratitude"
    CLOSING = "closing"


class Complexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class AgentName(str, Enum):
    ANALYTICAL = "analytical"   # maps to internal "risk" agent
    EMOTIONAL = "emotional"     # maps to internal "eq" agent
    ETHICAL = "ethical"
    VALUES = "values"
    RED_TEAM = "red_team"


class FeedbackType(str, Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    TOO_LONG = "too_long"
    TOO_SHORT = "too_short"
    OFF_TOPIC = "off_topic"
    TONE_WRONG = "tone_wrong"


class StepType(str, Enum):
    INTENT = "intent"
    COMPLEXITY = "complexity"
    MEMORY_RETRIEVAL = "memory_retrieval"
    AGENT_REASONING = "agent_reasoning"
    DEBATE_CRITIQUE = "debate_critique"
    CONFLICT_RESOLUTION = "conflict_resolution"
    PERSONALITY_STYLING = "personality_styling"
    RESPONSE_CONTROL = "response_control"
    FINAL_OUTPUT = "final_output"


# ========================= BRAIN CONFIG =========================

class BrainConfig(BaseModel):
    """User-controlled agent weight configuration."""
    analytical: float = Field(default=0.2, ge=0.0, le=1.0)
    emotional: float = Field(default=0.2, ge=0.0, le=1.0)
    ethical: float = Field(default=0.2, ge=0.0, le=1.0)
    values: float = Field(default=0.2, ge=0.0, le=1.0)
    red_team: float = Field(default=0.0, ge=0.0, le=1.0)

    def to_internal_weights(self) -> Dict[str, float]:
        """Map user-facing names to internal agent names."""
        return {
            "risk": self.analytical,
            "eq": self.emotional,
            "ethical": self.ethical,
            "values": self.values,
            "red_team": self.red_team,
        }

    def dominant_agent(self) -> AgentName:
        """Return the agent with the highest weight."""
        mapping = {
            AgentName.ANALYTICAL: self.analytical,
            AgentName.EMOTIONAL: self.emotional,
            AgentName.ETHICAL: self.ethical,
            AgentName.VALUES: self.values,
            AgentName.RED_TEAM: self.red_team,
        }
        return max(mapping, key=mapping.get)

    def active_agents(self) -> List[AgentName]:
        """Return agents with weight > 0, sorted by weight descending."""
        mapping = {
            AgentName.ANALYTICAL: self.analytical,
            AgentName.EMOTIONAL: self.emotional,
            AgentName.ETHICAL: self.ethical,
            AgentName.VALUES: self.values,
            AgentName.RED_TEAM: self.red_team,
        }
        return [k for k, v in sorted(mapping.items(), key=lambda x: -x[1]) if v > 0]


# ========================= AGENT OUTPUT =========================

class AgentOutput(BaseModel):
    """Structured output from a single cognitive agent."""
    agent: AgentName
    reasoning: str = Field(..., max_length=500)
    response: str = Field(..., max_length=300)
    confidence: float = Field(..., ge=0.0, le=1.0)


# ========================= THINKING TRACE =========================

class TraceStep(BaseModel):
    """Single step in the thinking trace."""
    step_type: StepType
    agent: Optional[AgentName] = None
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThinkingTrace(BaseModel):
    """Full thinking trace for a conversation turn."""
    conversation_id: str
    message_id: str
    steps: List[TraceStep] = Field(default_factory=list)

    def add_step(self, step_type: StepType, content: str, agent: Optional[AgentName] = None):
        self.steps.append(TraceStep(step_type=step_type, agent=agent, content=content))


# ========================= CLASSIFIER RESULTS =========================

class IntentResult(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)


class ComplexityResult(BaseModel):
    complexity: Complexity
    reasoning: str = ""


# ========================= API REQUEST / RESPONSE =========================

class ChatRequest(BaseModel):
    """Incoming chat message from the user."""
    query: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None  # None = start new conversation
    brain_weights: Optional[BrainConfig] = None  # None = use stored defaults
    tone: Optional[str] = Field(default="clean", description="User tone: clean, casual, blunt, blunt_profane")


class ChatResponse(BaseModel):
    """Response to the user."""
    response: str
    conversation_id: str
    message_id: str
    intent: Intent
    complexity: Complexity
    thinking_trace_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    """User feedback on a specific response."""
    conversation_id: str
    message_id: str
    rating: int = Field(..., ge=1, le=10)
    feedback_type: FeedbackType
    text_feedback: Optional[str] = Field(default=None, max_length=1000)
    brain_config: Optional[BrainConfig] = None


class FeedbackResponse(BaseModel):
    stored: bool
    evolution_triggered: bool = False
    preferred_brain_config: Optional[BrainConfig] = None


class TraceResponse(BaseModel):
    conversation_id: str
    steps: List[TraceStep]


# ========================= LANGGRAPH STATE =========================

class PipelineState(BaseModel):
    """
    State object flowing through the LangGraph pipeline.
    This is the single source of truth for the entire reasoning chain.
    """
    # Input
    user_query: str
    conversation_id: str
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Brain config
    brain_config: BrainConfig = Field(default_factory=BrainConfig)

    # Classification
    intent: Optional[Intent] = None
    complexity: Optional[Complexity] = None

    # Memory context (pre-built string for prompt injection)
    short_term_context: str = ""
    episodic_context: str = ""
    user_profile_context: str = ""

    # Agent outputs
    agent_outputs: List[AgentOutput] = Field(default_factory=list)

    # Debate
    critiques: List[Dict[str, Any]] = Field(default_factory=list)
    disagreement_score: float = 0.0

    # Synthesis
    resolved_reasoning: str = ""
    styled_response: str = ""
    final_response: str = ""

    # Thinking trace (accumulated through pipeline)
    trace: ThinkingTrace = None

    # Tone
    tone_instruction: str = ""

    class Config:
        arbitrary_types_allowed = True
