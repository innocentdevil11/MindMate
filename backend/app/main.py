"""
MindMate v3 — FastAPI Application Entry Point.

This is the new main application that registers v3 routers alongside
the existing v2 API. The old api.py remains functional for backward compatibility.

Run with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, feedback, trace, conversations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources at startup, clean up at shutdown."""
    # Compile the LangGraph workflow
    chat.init_graph()
    logger.info("MindMate v3 started successfully")
    yield
    logger.info("MindMate v3 shutting down")


app = FastAPI(
    title="MindMate v3 API",
    description=(
        "Multi-agent cognition platform with adaptive personality, "
        "debate-based reasoning, and brain evolution."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# CORS
# Supports explicit origins plus optional regex for dynamic preview domains.
cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:8001")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
cors_origin_regex = os.getenv(
    "BACKEND_CORS_ORIGIN_REGEX",
    r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
).strip() or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v3 routers
app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(trace.router)
app.include_router(conversations.router)

# Import and mount legacy v2 API for backward compatibility
try:
    from api import app as legacy_app
    app.mount("/v2", legacy_app)
    logger.info("Legacy v2 API mounted at /v2")
except ImportError:
    logger.warning("Legacy v2 API not available")


# ==================== HEALTH & INFO ====================

@app.get("/")
async def root():
    return {
        "name": "MindMate v3",
        "status": "operational",
        "version": "3.0.0",
        "endpoints": {
            "chat": "POST /chat",
            "feedback": "POST /feedback",
            "evolution": "GET /feedback/evolution",
            "trace": "GET /trace/{conversation_id}",
            "trace_summary": "GET /trace/{conversation_id}/summary",
            "health": "GET /health",
            "legacy": "/v2/* (backward compatible)",
        },
    }


@app.get("/health")
async def health():
    graph_ready = chat._graph is not None
    return {
        "status": "healthy" if graph_ready else "degraded",
        "graph_initialized": graph_ready,
        "version": "3.0.0",
    }
