from graph.graph import build_mindmate_graph
import json

if __name__ == "__main__":
    graph = build_mindmate_graph()

    initial_state = {
        "user_query": "Should I invest in cryptocurrency?",
        "weights": {
            "ethical": 0.2,
            "risk": 0.3,
            "eq": 0.2,
            "values": 0.2,
            "red_team": 0.1,
        },
        "agent_outputs": {},
        "final_answer": "",
    }

    result = graph.invoke(initial_state)

    print("\n================ AGENT OUTPUTS ================\n")

    for agent, data in result["agent_outputs"].items():
        print(f"--- {agent.upper()} AGENT ---")
        print(data["output"])
        print()

    print("\n================ FINAL DECISION ================\n")
    print(result["final_answer"])
