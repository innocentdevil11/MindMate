"""
Feedback Router — MindMate v3 API.

POST /feedback — Submit structured feedback and trigger brain evolution.
GET  /feedback/evolution — Get brain evolution status for the user.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from auth import get_current_user
from db import get_supabase_admin
from app.models.schemas import FeedbackRequest, FeedbackResponse, BrainConfig
from app.services.brain_evolution import compute_evolved_defaults, get_evolution_status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Submit structured feedback on a response.
    Stores the feedback and triggers brain evolution computation.
    """
    try:
        sb = get_supabase_admin()

        # Store feedback
        payload = {
            "user_id": user_id,
            "conversation_id": request.conversation_id,
            "message_id": request.message_id,
            "rating": request.rating,
            "feedback_type": request.feedback_type.value,
            "text_feedback": request.text_feedback,
            "brain_config": request.brain_config.model_dump() if request.brain_config else None,
        }

        result = sb.table("feedback_v2").insert(payload).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to store feedback")

        # Trigger brain evolution
        evolution_triggered = False
        preferred_config = None

        evolved = await compute_evolved_defaults(user_id)
        if evolved:
            evolution_triggered = True
            preferred_config = evolved

        logger.info(f"Feedback stored for user {user_id[:8]}, evolution={evolution_triggered}")

        return FeedbackResponse(
            stored=True,
            evolution_triggered=evolution_triggered,
            preferred_brain_config=preferred_config,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/evolution")
async def get_brain_evolution(
    user_id: str = Depends(get_current_user),
):
    """Get the user's brain evolution status and current defaults."""
    try:
        status = await get_evolution_status(user_id)
        return status
    except Exception as e:
        logger.error(f"Evolution status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
