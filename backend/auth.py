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
import json
import base64
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db import get_supabase, get_supabase_admin, SUPABASE_URL

logger = logging.getLogger(__name__)

# FastAPI security scheme — extracts "Bearer <token>" from Authorization header
_bearer_scheme = HTTPBearer(auto_error=False)


def _extract_project_ref_from_token(token: str) -> Optional[str]:
    """Best-effort decode of JWT payload to extract Supabase project ref from `iss`."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload = parts[1]
        padding = "=" * ((4 - len(payload) % 4) % 4)
        decoded = base64.urlsafe_b64decode((payload + padding).encode("utf-8"))
        data = json.loads(decoded.decode("utf-8"))
        iss = data.get("iss", "")
        # Expected: https://<project-ref>.supabase.co/auth/v1
        if isinstance(iss, str) and ".supabase.co/auth/v1" in iss:
            host = iss.replace("https://", "").split("/")[0]
            return host.split(".")[0]
    except Exception:
        return None
    return None


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
        # Detect token/project mismatch early to avoid opaque 401 loops.
        backend_ref = None
        if SUPABASE_URL and ".supabase.co" in SUPABASE_URL:
            backend_ref = SUPABASE_URL.replace("https://", "").split(".")[0]
        token_ref = _extract_project_ref_from_token(token)
        if backend_ref and token_ref and backend_ref != token_ref:
            logger.warning(f"Token project ref mismatch: token={token_ref}, backend={backend_ref}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token belongs to a different Supabase project. Sign out and sign in again.",
            )

        # Validate token via Supabase auth server.
        # Prefer admin client for backend-side reliability; fallback to anon client.
        try:
            user_response = get_supabase_admin().auth.get_user(token)
        except Exception:
            user_response = get_supabase().auth.get_user(token)

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
