"""
MindMate API — FastAPI backend.

Endpoints:
  Public:
    GET  /           - API info
    GET  /health     - Health check

  Authenticated (require Bearer token):
    POST /decision          - Execute multi-agent decision process
    GET  /preferences       - Get user preferences
    PUT  /preferences       - Update user preferences
    GET  /memory            - List user memories
    POST /memory            - Store a new memory
    POST /feedback          - Submit feedback on a response
"""

import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from graph.graph import build_mindmate_graph
from auth import get_current_user
from services import preferences as pref_service
from services import memory as memory_service
from services import contradiction as contradiction_service
from services import feedback as feedback_service

# Global graph instance
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize graph at startup"""
    global graph
    graph = build_mindmate_graph()
    yield
    # Cleanup if needed
    graph = None


app = FastAPI(
    title="MindMate API",
    description="Multi-agent decision system API with personalization",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration — supports production origins via env var
cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== PYDANTIC MODELS ====================

class Weights(BaseModel):
    ethical: float = Field(..., ge=0.0, le=1.0)
    risk: float = Field(..., ge=0.0, le=1.0)
    eq: float = Field(..., ge=0.0, le=1.0)
    values: float = Field(..., ge=0.0, le=1.0)
    red_team: float = Field(..., ge=0.0, le=1.0)


class DecisionRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    weights: Weights


class AgentOutputs(BaseModel):
    ethical: str
    risk: str
    eq: str
    values: str
    red_team: str


class ExplanationMetadata(BaseModel):
    """Feature 5: Observability metadata for debugging and trust."""
    tone_mode: str
    memory_labels_used: List[str]
    has_memory_context: bool
    response_confidence: float
    preference_confidence: Optional[float] = None


class DecisionResponse(BaseModel):
    agent_outputs: AgentOutputs
    final_decision: str
    explanation: Optional[ExplanationMetadata] = None


class PreferencesUpdate(BaseModel):
    tone_preference: Optional[str] = None
    default_weights: Optional[Dict[str, float]] = None
    confirm_contradiction: bool = False  # Set to True to override a flagged conflict


class MemoryCreate(BaseModel):
    type: str = Field(..., pattern="^(preference|pattern|outcome)$")
    label: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=1000)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class FeedbackCreate(BaseModel):
    query: str = Field(..., min_length=1)
    tone_alignment: Optional[str] = None
    usefulness: Optional[int] = Field(default=None, ge=1, le=10)
    outcome: Optional[str] = None


# ==================== PUBLIC ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "message": "MindMate API",
        "status": "operational",
        "version": "2.0.0",
        "endpoints": [
            "/decision", "/health", "/preferences",
            "/memory", "/feedback",
        ],
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "graph_initialized": graph is not None}


# ==================== DECISION (AUTHENTICATED) ====================

@app.post("/decision", response_model=DecisionResponse)
async def make_decision(
    request: DecisionRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Execute the MindMate decision process with personalization.

    Loads user preferences and memory, injects them into the graph,
    and returns explanation metadata alongside the decision.
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")

    try:
        # Load user preferences
        prefs = await pref_service.get_preferences(user_id)
        tone = prefs.get("tone_preference", "clean")

        # Retrieve and format memory context
        memories = await memory_service.retrieve_memories(user_id)
        memory_context = memory_service.format_memory_context(memories)

        # Apply memory decay (lightweight, runs each request)
        await memory_service.decay_memories(user_id)

        # Check for feedback-based adjustments
        adjustments = await feedback_service.compute_adjustments(user_id)
        preference_confidence = adjustments.get("confidence", 0.0)

        # Prepare initial state with personalization
        initial_state = {
            "user_query": request.query,
            "weights": {
                "ethical": request.weights.ethical,
                "risk": request.weights.risk,
                "eq": request.weights.eq,
                "values": request.weights.values,
                "red_team": request.weights.red_team,
            },
            "agent_outputs": {},
            "final_answer": "",
            # NEW: personalization context
            "user_id": user_id,
            "tone_preference": tone,
            "memory_context": memory_context,
            "explanation_metadata": {},
        }

        # Execute LangGraph workflow
        result = graph.invoke(initial_state)

        # Extract and format response
        agent_outputs = AgentOutputs(
            ethical=result["agent_outputs"]["ethical"]["output"],
            risk=result["agent_outputs"]["risk"]["output"],
            eq=result["agent_outputs"]["eq"]["output"],
            values=result["agent_outputs"]["values"]["output"],
            red_team=result["agent_outputs"]["red_team"]["output"],
        )

        # Build explanation metadata (Feature 5)
        raw_explanation = result.get("explanation_metadata", {})
        explanation = ExplanationMetadata(
            tone_mode=raw_explanation.get("tone_mode", tone),
            memory_labels_used=raw_explanation.get("memory_labels_used", []),
            has_memory_context=raw_explanation.get("has_memory_context", bool(memory_context)),
            response_confidence=raw_explanation.get("response_confidence", 0.5),
            preference_confidence=preference_confidence,
        )

        response = DecisionResponse(
            agent_outputs=agent_outputs,
            final_decision=result["final_answer"],
            explanation=explanation,
        )

        return response

    except KeyError as e:
        logger.error(f"KeyError in graph result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Missing expected output from graph: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unhandled error in /decision: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing decision: {str(e)}"
        )


# ==================== PREFERENCES (AUTHENTICATED) ====================

@app.get("/preferences")
async def get_preferences(user_id: str = Depends(get_current_user)):
    """Get current user preferences (tone, default weights)."""
    try:
        prefs = await pref_service.get_preferences(user_id)
        return prefs
    except Exception as e:
        logger.error(f"Error fetching preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/preferences")
async def update_preferences(
    data: PreferencesUpdate,
    user_id: str = Depends(get_current_user),
):
    """
    Update user preferences with contradiction detection.

    If a contradiction is detected (e.g., clean → blunt_profane),
    the response will include a conflict flag. Set confirm_contradiction=True
    to override.
    """
    try:
        # Feature 3: Contradiction detection before updating
        if data.tone_preference and not data.confirm_contradiction:
            conflict = await contradiction_service.check_preference_contradiction(
                user_id, "tone_preference", data.tone_preference
            )
            if conflict["conflict"]:
                return {
                    "conflict": True,
                    "message": conflict["message"],
                    "existing_value": conflict["existing_value"],
                    "action": "Set confirm_contradiction=True to proceed",
                }

        result = await pref_service.update_preferences(
            user_id, data.model_dump(exclude_none=True, exclude={"confirm_contradiction"})
        )
        return {"updated": True, "preferences": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MEMORY (AUTHENTICATED) ====================

@app.get("/memory")
async def list_memories(
    user_id: str = Depends(get_current_user),
    memory_type: Optional[str] = None,
):
    """List user memories, optionally filtered by type."""
    try:
        memories = await memory_service.retrieve_memories(
            user_id, memory_type=memory_type
        )
        return {"memories": memories, "count": len(memories)}
    except Exception as e:
        logger.error(f"Error fetching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory")
async def create_memory(
    data: MemoryCreate,
    user_id: str = Depends(get_current_user),
):
    """
    Store a structured memory entry with contradiction detection.

    If a memory with the same label already exists and differs,
    a conflict flag is returned.
    """
    try:
        # Feature 3: Check for contradicting existing memory
        conflict = await contradiction_service.check_memory_contradiction(
            user_id, data.type, data.label, data.content
        )
        if conflict["conflict"]:
            return {
                "conflict": True,
                "message": conflict["message"],
                "existing_content": conflict["existing_content"],
            }

        result = await memory_service.store_memory(
            user_id=user_id,
            memory_type=data.type,
            label=data.label,
            content=data.content,
            confidence=data.confidence,
        )
        return {"stored": True, "memory": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== FEEDBACK (AUTHENTICATED) ====================

@app.post("/feedback")
async def submit_feedback(
    data: FeedbackCreate,
    user_id: str = Depends(get_current_user),
):
    """
    Submit feedback on a decision response.

    Feedback influences future tone and retrieval weighting,
    but NEVER retrains or alters the model.
    """
    try:
        result = await feedback_service.store_feedback(
            user_id=user_id,
            query=data.query,
            tone_alignment=data.tone_alignment,
            usefulness=data.usefulness,
            outcome=data.outcome,
        )

        # Compute if any adjustments are now warranted
        adjustments = await feedback_service.compute_adjustments(user_id)

        return {
            "stored": True,
            "feedback": result,
            "adjustments": adjustments,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
