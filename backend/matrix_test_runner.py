import asyncio
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

from app.models.schemas import BrainConfig, AgentName
from app.routers.chat import init_graph, get_graph

load_dotenv()
init_graph()
graph = get_graph()

# Mute noisy loggers for the test output
logging.getLogger("app.services.personality_engine").setLevel(logging.WARNING)
logging.getLogger("app.services.debate_engine").setLevel(logging.WARNING)
logging.getLogger("app.langgraph.workflow").setLevel(logging.WARNING)

# Test Variables
BRAINS = {
    "Ethical": {"ethical": 1.0, "analytical": 0.0, "emotional": 0.0, "values": 0.0, "red_team": 0.0},
    "Analytical": {"ethical": 0.0, "analytical": 1.0, "emotional": 0.0, "values": 0.0, "red_team": 0.0},
    "Emotional": {"ethical": 0.0, "analytical": 0.0, "emotional": 1.0, "values": 0.0, "red_team": 0.0},
    "Values": {"ethical": 0.0, "analytical": 0.0, "emotional": 0.0, "values": 1.0, "red_team": 0.0},
    "Red_Team": {"ethical": 0.0, "analytical": 0.0, "emotional": 0.0, "values": 0.0, "red_team": 1.0},
}

TONES = ["clean", "casual", "blunt", "blunt_profane", "mentor", "philosophical", "supportive"]

QUERIES = [
    {
        "type": "Greeting (Simple)",
        "text": "Hi there"
    },
    {
        "type": "Factual (Medium)",
        "text": "What is the capital of France?"
    },
    {
        "type": "Dilemma (Complex)",
        "text": "My employee is stealing from the company, but he needs the money to pay for his child's medical bills. If I fire him, his kid might die. If I don't, the company might go bankrupt."
    }
]

async def run_combination(query_type: str, query_text: str, brain_name: str, weights: dict, tone: str) -> Dict[str, Any]:
    state = {
        "user_query": query_text,
        "conversation_id": f"test-{brain_name}-{tone}-{query_type}".replace(" ", "-").lower(),
        "message_id": "test-msg",
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

    try:
        result = await asyncio.to_thread(graph.invoke, state)
        
        return {
            "success": True,
            "intent": result.get("intent"),
            "complexity": result.get("complexity"),
            "agents_run": len(result.get("agent_outputs", [])),
            "debated": len(result.get("critiques", [])) > 0,
            "dispute_score": result.get("disagreement_score", 0.0),
            "response": result.get("final_response", ""),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def main():
    print("==========================================================")
    print("MINDMATE V3 COMPREHENSIVE MATRIX TEST REPORT")
    print("==========================================================\n")
    
    report_lines = []
    
    for query in QUERIES:
        print(f"\n# Category: {query['type']}")
        print(f"# Query: '{query['text']}'")
        report_lines.append(f"\n# Category: {query['type']}")
        report_lines.append(f"# Query: '{query['text']}'")
        
        for brain_name, weights in BRAINS.items():
            print(f"\n  --- Brain: {brain_name} ---")
            report_lines.append(f"\n  ## Brain: {brain_name}")
            
            for tone in TONES:
                print(f"    Testing Tone: {tone}...")
                res = await run_combination(query['type'], query['text'], brain_name, weights, tone)
                
                if not res["success"]:
                    line = f"    [ERROR] Tone: {tone} | Failed: {res['error']}"
                    print(line)
                    report_lines.append(line)
                    continue

                # Format the output block for the report
                report_lines.append(f"\n    ### Tone: {tone}")
                report_lines.append(f"    - **Intent:** {res['intent']} | **Complexity:** {res['complexity']}")
                report_lines.append(f"    - **Agents Spawned:** {res['agents_run']} | **Debate Triggered:** {res['debated']} (Score: {res['dispute_score']})")
                report_lines.append(f"    - **Output:** {res['response']}")

    # Write final extensive report to disk for review
    with open("matrix_test_report.md", "w", encoding="utf-8") as f:
        f.write("# MindMate V3 Matrix Test Report\n")
        f.write("\n".join(report_lines))
        
    print("\n==========================================================")
    print("MATRIX TEST COMPLETE. Results written to matrix_test_report.md")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(main())
