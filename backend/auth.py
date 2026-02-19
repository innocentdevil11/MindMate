"""
Authentication dependency — MindMate.

Verifies Supabase auth tokens and extracts user_id for request scoping.
Used as a FastAPI dependency: Depends(get_current_user).

WHY Supabase SDK verification instead of manual JWT decode:
- Supabase uses ES256 (asymmetric) JWTs, not HS256
- The SDK's get_user() validates against Supabase's auth server
- Handles token refresh, expiry, and algorithm changes automatically
- No need to manage JWKS keys or JWT secrets manually
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db import get_supabase

logger = logging.getLogger(__name__)

# FastAPI security scheme — extracts "Bearer <token>" from Authorization header
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency that validates the Supabase token and returns user_id.

    Uses Supabase SDK's get_user() which verifies the token against
    the Supabase auth server directly. This avoids manual JWT decoding
    and handles ES256/RS256/HS256 transparently.

    Usage:
        @app.get("/protected")
        async def protected(user_id: str = Depends(get_current_user)):
            ...

    Returns:
        str: The authenticated user's UUID (from Supabase auth.users.id)

    Raises:
        HTTPException 401: If token is missing, expired, or invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        sb = get_supabase()
        # Validate token via Supabase auth server
        user_response = sb.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        user_id = user_response.user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain a valid user ID",
            )

        return str(user_id)

    except HTTPException:
        raise  # Re-raise our own exceptions
    except Exception as e:
        logger.warning(f"Auth verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
