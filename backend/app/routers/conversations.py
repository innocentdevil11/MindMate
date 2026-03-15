"""
Conversations Router — MindMate v3 API.

GET /conversations — List all conversations for the active user
GET /conversations/{id} — Get history of a specific conversation
DELETE /conversations/{id} — Delete a conversation
"""

import logging
from typing import List, Dict

from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user
from db import get_supabase_admin
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversations"])

class ConversationListResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

class ConversationHistoryResponse(BaseModel):
    id: str
    title: str
    messages: List[MessageResponse]


class ConversationRenameRequest(BaseModel):
    title: str


@router.get("/conversations", response_model=List[ConversationListResponse])
async def list_conversations(user_id: str = Depends(get_current_user)):
    """Fetch all conversations for the authenticated user."""
    sb = get_supabase_admin()
    try:
        result = (
            sb.table("conversations")
            .select("id, title, created_at, updated_at")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch conversations: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation(conversation_id: str, user_id: str = Depends(get_current_user)):
    """Fetch details and all messages for a specific conversation."""
    sb = get_supabase_admin()
    try:
        # Check ownership and get title
        conv_resp = (
            sb.table("conversations")
            .select("id, title, user_id")
            .eq("id", conversation_id)
            .execute()
        )
        if not conv_resp.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if conv_resp.data[0]["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        title = conv_resp.data[0].get("title") or "New Conversation"

        # Get all messages
        msg_resp = (
            sb.table("messages")
            .select("id, role, content, created_at")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .execute()
        )
        
        return {
            "id": conversation_id,
            "title": title,
            "messages": msg_resp.data or []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch conversation history: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str = Depends(get_current_user)):
    """Delete a conversation and its nested messages (cascade via DB)."""
    sb = get_supabase_admin()
    try:
        # DB RLS/Ownership check can be done via exact match
        result = (
            sb.table("conversations")
            .delete()
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        # also delete messages natively just to be safe if cascade isn't fully robust
        sb.table("messages").delete().eq("conversation_id", conversation_id).execute()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.patch("/conversations/{conversation_id}/title")
async def rename_conversation(
    conversation_id: str,
    payload: ConversationRenameRequest,
    user_id: str = Depends(get_current_user),
):
    """Rename a conversation owned by the user."""
    from app.services.memory_service import update_conversation_title

    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    sb = get_supabase_admin()
    try:
        # Ownership check
        conv = (
            sb.table("conversations")
            .select("user_id")
            .eq("id", conversation_id)
            .limit(1)
            .execute()
        )
        if not conv.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conv.data[0]["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        await update_conversation_title(conversation_id, user_id, payload.title.strip())
        return {"status": "ok", "title": payload.title.strip()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rename conversation: {e}")
        raise HTTPException(status_code=500, detail="Database error")
