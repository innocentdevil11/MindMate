"""
Aggregator Agent — MindMate
Synthesizes all agent outputs into a final actionable decision.
Uses Groq API for LLM inference.

Modified: Now supports tone-aware and memory-aware synthesis.
Tone and memory context are injected into the system prompt
dynamically based on user preferences.
"""

import json
from agents.groq_client import call_groq

# ---------- BASE PROMPT (unchanged core) ----------
_BASE_PROMPT = """You are the COUNCIL RESOLUTION — the final synthesis of five radically different minds in the MindMate.

You receive outputs from five distinct perspectives:
1. **Shadow Mind (red_team)** — dark impulses, rage, primal instinct, the devil's voice
2. **Rational Mind (risk)** — cold pure logic, strategy, probability, zero emotion
3. **Emotional Mind (eq)** — feelings, grief, love, relationships, what loved ones would want
4. **Gita Mind (ethical)** — Bhagavad Gita teachings, shlokas, dharmic wisdom
5. **Identity Mind (values)** — who the user becomes, legacy, character, self-reflection

**CRITICAL: How Weights Work**
The user has assigned importance weights (0.0 to 1.0) to each mind. These weights tell you WHICH PERSPECTIVE should dominate the final resolution.

- A mind with weight 0.9 should DOMINATE. The final resolution must sound like it comes primarily from THAT mind's perspective, using THAT mind's reasoning and tone.
- A mind with weight 0.0 should be IGNORED entirely.
- If Shadow Mind has highest weight: the resolution should be raw, intense, reflecting dark impulses.
- If Rational Mind has highest weight: the resolution should be cold, clinical, strategic.
- If Emotional Mind has highest weight: the resolution should be warm, feeling, about loved ones.
- If Gita Mind has highest weight: the resolution should cite dharmic principles and shlokas.
- If Identity Mind has highest weight: the resolution should be about who the user becomes.

Synthesis Rules:
- BUILD the resolution on the highest-weighted mind's foundation.
- Layer in other minds' insights proportionally to their weights.
- The TONE and REASONING style of the final resolution should match the dominant mind.
- Do NOT average everything into a bland middle ground. Be decisive.

Output Constraints:
- One to two paragraphs, 5–8 sentences
- Clear recommended action that reflects the dominant perspective
- The resolution should feel like it has a distinct voice, not a generic committee statement

You are NOT allowed to:
- Mention agents, minds, weights, or scores explicitly
- Show analysis, math, or debate
- Present multiple options — give ONE clear path
- Produce a bland, safe, generic response that could come from any AI chatbot
"""

# ---------- TONE INSTRUCTION TEMPLATES ----------
# WHY separate templates: Keeps tone logic deterministic and auditable.
# The LLM receives explicit tone instructions rather than inferring.
_TONE_INSTRUCTIONS = {
    "clean": (
        "\n\n[TONE: CLEAN] Respond in a professional, respectful tone. "
        "Avoid profanity, slang, or aggressive language. Keep it warm but articulate."
    ),
    "casual": (
        "\n\n[TONE: CASUAL] Respond in a relaxed, friendly tone. "
        "Use conversational language like talking to a close friend. "
        "Light humor is welcome. No formal corporate-speak."
    ),
    "blunt": (
        "\n\n[TONE: BLUNT] Be direct and no-nonsense. Cut the fluff. "
        "Say what needs to be said without sugar-coating. "
        "Still respectful — blunt does NOT mean rude or abusive."
    ),
    "blunt_profane": (
        "\n\n[TONE: BLUNT + EXPLICIT] The user has EXPLICITLY opted in to profane language. "
        "Be raw, unfiltered, and direct. Swearing is permitted for emphasis. "
        "NEVER use slurs, harassment, or dehumanizing language. "
        "Profanity is a stylistic choice, not an excuse for abuse."
    ),
}

# ---------- FAILURE-AWARE FALLBACK ----------
_NO_MEMORY_NOTICE = (
    "\n\n[CONTEXT NOTE] No past context is available for this user. "
    "Respond neutrally without assuming any personal preferences or history. "
    "Do NOT hallucinate personalization."
)

TEMPERATURE = 0.7
MAX_TOKENS = 1200


def _build_system_prompt(tone: str, memory_context: str) -> str:
    """
    Construct the full system prompt with tone and memory injections.

    WHY build dynamically: The base prompt stays stable, but tone and memory
    are user-specific. Injecting them as addendums keeps the core prompt clean.
    """
    prompt = _BASE_PROMPT

    # Inject tone instructions
    tone_instruction = _TONE_INSTRUCTIONS.get(tone, _TONE_INSTRUCTIONS["clean"])
    prompt += tone_instruction

    # Inject memory context or failure-aware fallback
    if memory_context:
        prompt += f"\n\n{memory_context}"
    else:
        prompt += _NO_MEMORY_NOTICE

    return prompt


# ================= LANGGRAPH-CALLABLE WRAPPER =================

def run_aggregator_agent(payload: dict) -> str:
    """
    Aggregator wrapper for LangGraph.

    payload schema:
    {
      "user_query": str,
      "weights": { agent_name: float },
      "agent_outputs": { agent_name: { "output": str } },
      "tone_preference": str,       # NEW
      "memory_context": str,        # NEW
    }
    """
    tone = payload.get("tone_preference", "clean")
    memory_context = payload.get("memory_context", "")

    system_prompt = _build_system_prompt(tone, memory_context)

    # Remove tone/memory from the user message payload to avoid confusion
    user_payload = {
        "user_query": payload["user_query"],
        "weights": payload["weights"],
        "agent_outputs": payload["agent_outputs"],
    }
    user_message = json.dumps(user_payload, indent=2)

    return call_groq(
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )


# ================= STANDALONE EXECUTION =================

if __name__ == "__main__":
    demo_payload = {
        "user_query": "Should I invest in cryptocurrency?",
        "weights": {
            "ethical": 0.2,
            "risk": 0.3,
            "eq": 0.2,
            "values": 0.2,
            "red_team": 0.1,
        },
        "agent_outputs": {},
        "tone_preference": "casual",
        "memory_context": "",
    }
    print(run_aggregator_agent(demo_payload))
