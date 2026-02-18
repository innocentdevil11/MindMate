from langgraph.graph import StateGraph, START, END

from graph.state import SynapseState
from graph.nodes import (
    ethical_node,
    eq_node,
    risk_node,
    red_team_node,
    values_node,
    aggregator_node,
)


def build_mindmate_graph():
    graph = StateGraph(SynapseState)

    # Register nodes
    graph.add_node("ethical", ethical_node)
    graph.add_node("eq", eq_node)
    graph.add_node("risk", risk_node)
    graph.add_node("red_team", red_team_node)
    graph.add_node("values", values_node)
    graph.add_node("aggregator", aggregator_node)

    # TRUE parallel: all 5 agents start simultaneously from START
    graph.add_edge(START, "ethical")
    graph.add_edge(START, "eq")
    graph.add_edge(START, "risk")
    graph.add_edge(START, "red_team")
    graph.add_edge(START, "values")

    # Fan-in: all agents feed into aggregator
    graph.add_edge("ethical", "aggregator")
    graph.add_edge("eq", "aggregator")
    graph.add_edge("risk", "aggregator")
    graph.add_edge("red_team", "aggregator")
    graph.add_edge("values", "aggregator")

    # End
    graph.add_edge("aggregator", END)

    return graph.compile()
