"""
Trace Router — MindMate v3 API.

GET /trace/{conversation_id} — Retrieve thinking trace for a conversation.

The thinking trace shows the internal reasoning pipeline:
  - Intent classification
  - Complexity routing
  - Agent reasoning outputs
  - Debate critiques (if applicable)
  - Conflict resolution
  - Personality styling
  - Response length control
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from auth import get_current_user
from db import get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["trace"])


def _assert_conversation_owner(sb, conversation_id: str, user_id: str) -> None:
    conv = (
        sb.table("conversations")
        .select("id, user_id")
        .eq("id", conversation_id)
        .limit(1)
        .execute()
    )
    if not conv.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.data[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")


@router.get("/trace/{conversation_id}")
async def get_trace(
    conversation_id: str,
    message_id: Optional[str] = Query(None, description="Filter by specific message"),
    user_id: str = Depends(get_current_user),
):
    """
    Retrieve the thinking trace for a conversation.

    Returns all reasoning steps in chronological order.
    Optionally filter by a specific message_id.
    """
    try:
        sb = get_supabase_admin()
        _assert_conversation_owner(sb, conversation_id, user_id)

        query = (
            sb.table("thinking_trace")
            .select("id, step_type, agent, content, message_id, created_at")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
        )

        if message_id:
            query = query.eq("message_id", message_id)

        result = query.execute()
        steps = result.data or []

        return {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "step_count": len(steps),
            "steps": steps,
        }

    except Exception as e:
        logger.error(f"Trace retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trace/{conversation_id}/summary")
async def get_trace_summary(
    conversation_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Get a condensed summary of the thinking process for a conversation.
    Groups steps by message and returns high-level flow.
    """
    try:
        sb = get_supabase_admin()
        _assert_conversation_owner(sb, conversation_id, user_id)

        result = (
            sb.table("thinking_trace")
            .select("message_id, step_type, agent")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .execute()
        )

        steps = result.data or []

        # Group by message_id
        messages = {}
        for step in steps:
            mid = step["message_id"]
            if mid not in messages:
                messages[mid] = {
                    "message_id": mid,
                    "pipeline": [],
                    "agents_used": set(),
                }
            messages[mid]["pipeline"].append(step["step_type"])
            if step.get("agent"):
                messages[mid]["agents_used"].add(step["agent"])

        # Convert sets to lists for JSON serialization
        summary = []
        for mid, data in messages.items():
            summary.append({
                "message_id": data["message_id"],
                "pipeline_steps": data["pipeline"],
                "agents_used": list(data["agents_used"]),
            })

        return {
            "conversation_id": conversation_id,
            "message_count": len(summary),
            "messages": summary,
        }

    except Exception as e:
        logger.error(f"Trace summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
