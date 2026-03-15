import asyncio
import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

from app.models.schemas import ChatRequest, BrainConfig
from app.routers.chat import init_graph, get_graph

load_dotenv()

# We need a valid JWT token to bypass auth dependencies if doing full API test
# But we can just test the graph directly to isolate the routing logic
init_graph()
graph = get_graph()

async def run_test(name: str, query: str, weights: dict, tone: str = "clean"):
    print(f"\n=======================================================")
    print(f"TEST: {name}")
    print(f"QUERY: '{query}'")
    print(f"WEIGHTS: {weights}")
    print(f"TONE: {tone}")
    print(f"=======================================================\n")

    initial_state = {
        "user_query": query,
        "conversation_id": f"test-conv-{name.replace(' ', '-').lower()}",
        "message_id": f"test-msg-1",
        "user_id": "test-user",
        "brain_config": BrainConfig(**weights).model_dump(),
        "memory_context": "",
        "intent": "",
        "complexity": "",
        "conversation_depth": 0,
        "agent_outputs": [],
        "critiques": [],
        "disagreement_score": 0.0,
        "synthesis_suggestion": "",
        "resolved_reasoning": "",
        "resolved_response": "",
        "tone_instruction": tone,
        "final_response": "",
        "trace_steps": [],
    }

    print("Running pipeline...")
    result = graph.invoke(initial_state)

    print(f"\n[RESULTS]")
    print(f"Intent:     {result.get('intent')}")
    print(f"Complexity: {result.get('complexity')}")
    print(f"Tone setup: {result.get('tone_instruction', '').splitlines()[0]}")

    agents_run = [o.get('agent') for o in result.get('agent_outputs', [])]
    print(f"Agents run: {agents_run}")

    critiques = result.get('critiques', [])
    print(f"Debate:     {'YES (' + str(len(critiques)) + ' critiques)' if critiques else 'NO'}")
    print(f"Dispute:    {result.get('disagreement_score')}")

    print(f"\nFINAL REASONING:")
    print(result.get('resolved_reasoning', 'N/A (simple path)'))

    print(f"\nFINAL RESPONSE:")
    print(result.get('final_response'))

    return result

async def main():
    # TEST 1: High Emotional, Very complex query
    # Should run agents, emotional should dominate synthesis, debate should evaluate eq vs others
    await run_test(
        name="High EQ Complex Dilemma",
        query="I discovered my co-founder has been secretly taking small amounts of money from the business. We've been best friends for 10 years and his wife is currently undergoing cancer treatment, which is why he said he needed it. If I report him, the company tanks and he goes to jail. If I don't, I'm complicit in fraud. I feel completely torn apart and betrayed, but also deeply sympathetic.",
        weights={
            "emotional": 0.8,
            "analytical": 0.1,
            "ethical": 0.1,
            "values": 0.0,
            "red_team": 0.0
        },
        tone="supportive"
    )

    # TEST 2: High Analytical + Red Team, Same query
    # Responses should completely shift tone and focus, debate should be stark
    await run_test(
        name="High Logic/Red Team Challenge",
        query="I discovered my co-founder has been secretly taking small amounts of money from the business. We've been best friends for 10 years and his wife is currently undergoing cancer treatment, which is why he said he needed it. If I report him, the company tanks and he goes to jail. If I don't, I'm complicit in fraud. I feel completely torn apart and betrayed, but also deeply sympathetic.",
        weights={
            "emotional": 0.0,
            "analytical": 0.6,
            "ethical": 0.0,
            "values": 0.0,
            "red_team": 0.4
        },
        tone="blunt_profane"
    )

    # TEST 3: Pure Ethical, Medium query
    # No debate expected, just direct ethical synthesis
    await run_test(
        name="Pure Ethics Advice",
        query="Is it okay to lie on my resume about my degree if the job doesn't actually require the skills I learned in college?",
        weights={
            "emotional": 0.0,
            "analytical": 0.0,
            "ethical": 1.0,
            "values": 0.0,
            "red_team": 0.0
        },
        tone="philosophical"
    )

if __name__ == "__main__":
    asyncio.run(main())
