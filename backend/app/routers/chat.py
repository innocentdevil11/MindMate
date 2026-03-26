"""
Chat Router — MindMate v3 API.

POST /chat — Main conversational endpoint.
Handles the full pipeline: auth → memory → brain config → LangGraph → store → respond.
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from auth import get_current_user
from app.models.schemas import (
    ChatRequest, ChatResponse, BrainConfig,
    Intent, Complexity,
)
from app.services.brain_engine import load_brain_config, create_conversation_id
from app.services.memory_service import (
    store_message, get_short_term_context,
    get_conversation_depth, build_memory_context,
    create_conversation_record, get_conversation_metadata,
    update_conversation_title, touch_conversation, update_conversation_configs,
)
from app.langgraph.workflow import build_mindmate_v3_graph
from agents.groq_client import call_groq

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

# Global compiled graph — initialized at app startup
_graph = None


def init_graph():
    """Compile the LangGraph workflow. Called once at app startup."""
    global _graph
    _graph = build_mindmate_v3_graph()
    logger.info("MindMate v3 graph compiled successfully")


def get_graph():
    """Get the compiled graph instance."""
    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    return _graph


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Main conversational endpoint.

        Pipeline:
            1. Resolve conversation ID (new or existing)
            2. Ensure conversation record exists
            3. Store user message
            4. Load brain config
            5. Build memory context
            6. Execute LangGraph cognitive pipeline
            7. Store AI response
            8. Store thinking trace
            9. Return response
    """
    graph = get_graph()

    try:
        # Step 1: Resolve conversation
        conversation_id = request.conversation_id or create_conversation_id()
        message_id = str(uuid.uuid4())

        # Step 2: Load latest conversation metadata
        convo_meta = await get_conversation_metadata(conversation_id)
        if convo_meta and convo_meta.get("user_id") and convo_meta.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Conversation does not belong to user")

        # Step 3: Determine brain/tone configs (fresh per message)
        # Priority: request override > stored conversation configs > brain_config table fallback
        if request.brain_weights:
            brain_config = request.brain_weights
        elif convo_meta and convo_meta.get("brain_config"):
            brain_config = BrainConfig(**convo_meta["brain_config"])
        else:
            brain_config = await load_brain_config(
                conversation_id=conversation_id,
                user_id=user_id,
                override=None,
            )

        tone_config = request.tone or (convo_meta.get("tone_config") if convo_meta else "clean") or "clean"

        # Ensure conversation record exists and is updated with current configs
        if not convo_meta:
            await create_conversation_record(
                conversation_id=conversation_id,
                user_id=user_id,
                title=None,
                brain_config=brain_config.model_dump(),
                tone_config=tone_config,
            )
        else:
            await update_conversation_configs(
                conversation_id=conversation_id,
                user_id=user_id,
                brain_config=brain_config.model_dump(),
                tone_config=tone_config,
            )

        # Also persist to brain_config table for backward compat / evolution
        await load_brain_config(
            conversation_id=conversation_id,
            user_id=user_id,
            override=brain_config,
        )

        # Step 4: Store user message
        await store_message(conversation_id, user_id, "user", request.query)
        await touch_conversation(
            conversation_id,
            user_id,
            brain_config=brain_config.model_dump(),
            tone_config=tone_config,
        )

        # Step 4: Build memory context
        conversation_depth = await get_conversation_depth(conversation_id)
        memory = await build_memory_context(
            conversation_id=conversation_id,
            user_id=user_id,
            # Note: episodic memory embedding requires a separate embedding call
            # For now, skip episodic until embedding service is configured
            query_embedding=None,
        )

        # Combine memory layers into a single context string
        memory_parts = [v for v in memory.values() if v]
        combined_memory = "\n\n".join(memory_parts)

        # Step 5: Execute LangGraph with timeout guard
        initial_state = {
            "user_query": request.query,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "user_id": user_id,
            "brain_config": brain_config.model_dump(),
            "memory_context": combined_memory,
            "intent": "",
            "complexity": "",
            "conversation_depth": conversation_depth,
            "agent_outputs": [],
            "critiques": [],
            "disagreement_score": 0.0,
            "synthesis_suggestion": "",
            "resolved_reasoning": "",
            "resolved_response": "",
            "tone_instruction": tone_config,
            "final_response": "",
            "conversation_mode": "normal",
            "trace_steps": [],
        }

        # Run the graph pipeline directly
        result = graph.invoke(initial_state)

        # Empty-response fallback — guarantee we ALWAYS return something
        final_response = (result.get("final_response") or "").strip()
        if not final_response:
            logger.warning("Empty response from pipeline — using fallback")
            fallback = call_groq(
                system_prompt="You are MindMate, a thoughtful AI companion. Respond naturally and briefly.",
                user_message=request.query,
                temperature=0.7,
                max_tokens=100,
            )
            final_response = (fallback or "").strip() or "Hey — I'm here. What's on your mind?"

        # Step 6: Store AI response
        await store_message(conversation_id, user_id, "assistant", final_response)
        await touch_conversation(
            conversation_id,
            user_id,
            brain_config=brain_config.model_dump(),
            tone_config=tone_config,
        )

        # Auto-title on the FIRST turn (depth == 0) using the full first exchange
        if not (convo_meta and convo_meta.get("title")) and conversation_depth == 0:
            try:
                title = _generate_conversation_title_exchange(request.query, final_response)
                await update_conversation_title(conversation_id, user_id, title)
            except Exception as title_err:
                logger.warning(f"Failed to generate conversation title: {title_err}")

        # Step 7: Store thinking trace
        trace_steps = result.get("trace_steps", [])
        await _store_trace(conversation_id, message_id, trace_steps)

        # Step 8: Return response
        return ChatResponse(
            response=final_response,
            conversation_id=conversation_id,
            message_id=message_id,
            intent=Intent(result.get("intent", "smalltalk")),
            complexity=Complexity(result.get("complexity", "simple")),
            thinking_trace_id=message_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat pipeline error: {e}", exc_info=True)
        # Return a valid response instead of crashing
        fallback_msg = "I'm having trouble processing that right now. Could you try again?"
        try:
            await store_message(conversation_id, user_id, "assistant", fallback_msg)
        except Exception:
            pass
        return ChatResponse(
            response=fallback_msg,
            conversation_id=conversation_id,
            message_id=message_id,
            intent=Intent.SMALLTALK,
            complexity=Complexity.SIMPLE,
            thinking_trace_id=message_id,
        )


def _generate_conversation_title_exchange(user_query: str, ai_response: str) -> str:
    """Generate a short conversation title summarizing the first exchange."""
    context_to_summarize = f"User: {user_query}\nAI: {ai_response}".strip()
    
    prompt = (
        "You generate concise chat titles. "
        "Given the opening exchange of a conversation, respond with a 3-6 word title that summarizes the core topic. "
        "No quotes, no emojis, no punctuation. Title Case."
    )

    raw = call_groq(
        system_prompt=prompt,
        user_message=context_to_summarize[:1000],  # Give it enough context to summarize
        temperature=0.4,
        max_tokens=24,
    )

    cleaned = raw.strip().strip('"').strip("'")
    return cleaned[:80] or "New Conversation"


async def _store_trace(
    conversation_id: str,
    message_id: str,
    trace_steps: list,
) -> None:
    """Store thinking trace steps in the database."""
    from db import get_supabase_admin

    if not trace_steps:
        return

    sb = get_supabase_admin()
    rows = []
    for step in trace_steps:
        rows.append({
            "conversation_id": conversation_id,
            "message_id": message_id,
            "step_type": step.get("step_type", "unknown"),
            "agent": step.get("agent"),
            "content": step.get("content", ""),
        })

    try:
        sb.table("thinking_trace").insert(rows).execute()
    except Exception as e:
        logger.warning(f"Failed to store thinking trace: {e}")
