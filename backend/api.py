import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from graph.graph import build_mindmate_graph

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
    description="Multi-agent decision system API",
    version="1.0.0",
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


# Pydantic Models
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


class DecisionResponse(BaseModel):
    agent_outputs: AgentOutputs
    final_decision: str


@app.get("/")
async def root():
    return {
        "message": "MindMate API",
        "status": "operational",
        "endpoints": ["/decision", "/health"]
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "graph_initialized": graph is not None}


@app.post("/decision", response_model=DecisionResponse)
async def make_decision(request: DecisionRequest):
    """
    Execute the MindMate decision process.

    Takes a user query and agent weights, runs the LangGraph workflow,
    and returns all agent outputs plus the final aggregated decision.
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")

    try:
        # Prepare initial state
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

        response = DecisionResponse(
            agent_outputs=agent_outputs,
            final_decision=result["final_answer"]
        )

        return response

    except KeyError as e:
        logger.error(f"KeyError in graph result: {e}")
        logger.error(f"Graph result: {result}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
