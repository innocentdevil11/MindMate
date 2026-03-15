import asyncio
from dotenv import load_dotenv

from app.models.schemas import BrainConfig
from app.routers.chat import init_graph, get_graph

load_dotenv()
init_graph()
graph = get_graph()

async def run_test(name: str, query: str, weights: dict, tone: str):
    print(f"\n=======================================================")
    print(f"TEST: {name}")
    print(f"QUERY: '{query}'")
    print(f"WEIGHTS: {weights}")
    print(f"TONE: {tone}")
    print(f"=======================================================\n")

    initial_state = {
        "user_query": query,
        "conversation_id": f"test-ethical-{name.replace(' ', '-').lower()}",
        "message_id": f"test-msg-2",
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

    result = graph.invoke(initial_state)

    print(f"Intent:     {result.get('intent')}")
    print(f"Complexity: {result.get('complexity')}")
    print(f"\nFINAL RESPONSE:")
    print(result.get('final_response'))

async def main():
    # What the user originally experienced (Ethical brain + blunt tone)
    await run_test(
        name="Ethical Brain with Blunt Tone (Bug)",
        query="hi",
        weights={"ethical": 1.0, "analytical": 0.0, "emotional": 0.0, "values": 0.0, "red_team": 0.0},
        tone="blunt_profane"
    )

    # What the user expects (Ethical brain + clean tone)
    await run_test(
        name="Ethical Brain with Clean Tone (Fix)",
        query="hi",
        weights={"ethical": 1.0, "analytical": 0.0, "emotional": 0.0, "values": 0.0, "red_team": 0.0},
        tone="clean"
    )

if __name__ == "__main__":
    asyncio.run(main())
