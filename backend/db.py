"""
Supabase client module — MindMate.

Provides TWO Supabase clients:
1. get_supabase()       — Uses ANON key for client-side auth verification
2. get_supabase_admin() — Uses SERVICE ROLE key for trusted server-side DB queries

WHY two clients:
- The anon key respects RLS policies (needed for auth.get_user())
- The service role key bypasses RLS (needed for server-side CRUD where
  the backend has already verified the user via get_current_user)
"""

import os
import logging
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Load .env from backend directory
_backend_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=_backend_dir / ".env", override=True)

def _getenv_stripped(name: str):
    value = os.getenv(name)
    return value.strip() if isinstance(value, str) else value


SUPABASE_URL = _getenv_stripped("SUPABASE_URL")
SUPABASE_ANON_KEY = _getenv_stripped("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = _getenv_stripped("SUPABASE_SERVICE_ROLE_KEY")


def _ensure_no_proxy_for_supabase() -> None:
    """
    Ensure Supabase traffic bypasses machine-level proxy settings.

    Some local setups inject HTTP(S)_PROXY to localhost placeholders, which
    can break Supabase auth calls and surface as false 401s.
    """
    if not SUPABASE_URL:
        return

    host = urlparse(SUPABASE_URL).hostname
    if not host:
        return

    for key in ("NO_PROXY", "no_proxy"):
        raw = os.getenv(key, "")
        items = [entry.strip() for entry in raw.split(",") if entry.strip()]
        if host not in items:
            items.append(host)
            os.environ[key] = ",".join(items)


_ensure_no_proxy_for_supabase()

# Singletons
_client: Client | None = None
_admin_client: Client | None = None


def get_supabase() -> Client:
    """Get Supabase client with ANON key (for auth verification)."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set in backend/.env"
            )
        _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("Supabase anon client initialized")
    return _client


def get_supabase_admin() -> Client:
    """
    Get Supabase client with SERVICE ROLE key (bypasses RLS).

    Use this for all server-side database operations where the
    backend has already authenticated the user via get_current_user().
    """
    global _admin_client
    if _admin_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env"
            )
        _admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase admin client initialized")
    return _admin_client
