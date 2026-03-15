"""
MindMate v3 — End-to-end test script.
Tests the complete /chat pipeline with a real Supabase auth token.

Usage: python test_v3.py
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load env
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

API_BASE = "http://localhost:8001"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


def get_test_token():
    """Get a valid auth token. Uses existing session or creates test user."""
    sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    # Try to sign in with a test account
    TEST_EMAIL = "test@mindmate.dev"
    TEST_PASS = "testpass123456"
    
    try:
        result = sb.auth.sign_in_with_password({"email": TEST_EMAIL, "password": TEST_PASS})
        print(f"✓ Signed in as {TEST_EMAIL}")
        return result.session.access_token
    except Exception as e:
        print(f"  Sign-in failed: {e}")
        print(f"  Trying to create test account...")
        try:
            result = sb.auth.sign_up({"email": TEST_EMAIL, "password": TEST_PASS})
            if result.session:
                print(f"✓ Created and signed in as {TEST_EMAIL}")
                return result.session.access_token
            else:
                print(f"✗ Sign-up returned no session (email confirmation may be required)")
                print(f"  Go to Supabase Dashboard → Authentication → Settings")
                print(f"  Disable 'Confirm email' under Email Auth, then re-run this script")
                return None
        except Exception as e2:
            print(f"✗ Sign-up also failed: {e2}")
            return None


def test_health():
    """Test GET /health"""
    print("\n--- Test: GET /health ---")
    r = requests.get(f"{API_BASE}/health")
    print(f"  Status: {r.status_code}")
    print(f"  Body: {json.dumps(r.json(), indent=2)}")
    assert r.status_code == 200
    assert r.json()["graph_initialized"] == True
    print("  ✓ PASS")


def test_root():
    """Test GET /"""
    print("\n--- Test: GET / ---")
    r = requests.get(f"{API_BASE}/")
    print(f"  Status: {r.status_code}")
    data = r.json()
    assert data["version"] == "3.0.0"
    assert "chat" in data["endpoints"]
    print("  ✓ PASS")


def test_chat_greeting(token):
    """Test simple greeting (should take the SIMPLE path — no agents)."""
    print("\n--- Test: POST /chat (greeting) ---")
    r = requests.post(
        f"{API_BASE}/chat",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": "Hey, how are you?"},
        timeout=30,
    )
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Intent: {data.get('intent')}")
        print(f"  Complexity: {data.get('complexity')}")
        print(f"  Response: {data.get('response', '')[:200]}")
        print(f"  Conversation ID: {data.get('conversation_id')}")
        assert data.get("intent") in ("greeting", "smalltalk")
        assert data.get("complexity") == "simple"
        print("  ✓ PASS")
        return data
    else:
        print(f"  Body: {r.text[:500]}")
        print("  ✗ FAIL")
        return None


def test_chat_complex(token):
    """Test complex query (should trigger agents + potentially debate)."""
    print("\n--- Test: POST /chat (complex query) ---")
    r = requests.post(
        f"{API_BASE}/chat",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "query": "I'm torn between quitting my stable job to start a business or staying safe. I have a family to support and I don't know what to do. Help me decide.",
            "brain_weights": {
                "analytical": 0.3,
                "emotional": 0.3,
                "ethical": 0.15,
                "values": 0.2,
                "red_team": 0.05,
            },
        },
        timeout=60,
    )
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Intent: {data.get('intent')}")
        print(f"  Complexity: {data.get('complexity')}")
        print(f"  Response: {data.get('response', '')[:300]}")
        print(f"  Conversation ID: {data.get('conversation_id')}")
        print(f"  Trace ID: {data.get('thinking_trace_id')}")
        assert data.get("complexity") in ("medium", "complex")
        print("  ✓ PASS")
        return data
    else:
        print(f"  Body: {r.text[:500]}")
        print("  ✗ FAIL")
        return None


def test_trace(token, conversation_id):
    """Test GET /trace/{conversation_id}"""
    print(f"\n--- Test: GET /trace/{conversation_id[:8]}... ---")
    r = requests.get(
        f"{API_BASE}/trace/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Step count: {data.get('step_count')}")
        for step in data.get("steps", []):
            agent = step.get("agent") or "—"
            print(f"    [{step['step_type']}] ({agent}) {step['content'][:100]}")
        print("  ✓ PASS")
    else:
        print(f"  Body: {r.text[:300]}")
        print("  ✗ FAIL")


def test_feedback(token, conversation_id, message_id):
    """Test POST /feedback"""
    print(f"\n--- Test: POST /feedback ---")
    r = requests.post(
        f"{API_BASE}/feedback",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "conversation_id": conversation_id,
            "message_id": message_id,
            "rating": 4,
            "feedback_type": "thumbs_up",
            "brain_config": {
                "analytical": 0.3,
                "emotional": 0.3,
                "ethical": 0.15,
                "values": 0.2,
                "red_team": 0.05,
            },
        },
        timeout=10,
    )
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Stored: {data.get('stored')}")
        print(f"  Evolution triggered: {data.get('evolution_triggered')}")
        print("  ✓ PASS")
    else:
        print(f"  Body: {r.text[:300]}")
        print("  ✗ FAIL")


if __name__ == "__main__":
    print("=" * 60)
    print("  MindMate v3 — End-to-End Tests")
    print("=" * 60)

    # Health & root (no auth needed)
    test_health()
    test_root()

    # Get auth token
    token = get_test_token()
    if not token:
        print("\n✗ Cannot proceed without auth token.")
        exit(1)

    # Chat tests
    greeting_result = test_chat_greeting(token)
    complex_result = test_chat_complex(token)

    # Trace test (if complex chat succeeded)
    if complex_result:
        test_trace(token, complex_result["conversation_id"])
        test_feedback(token, complex_result["conversation_id"], complex_result["message_id"])

    print("\n" + "=" * 60)
    print("  All tests completed!")
    print("=" * 60)
