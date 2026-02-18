from agents.ethical_agent_file import run_ethical_agent
from agents.eq_agent import run_eq_agent
from agents.risk_logic_agent import run_risk_agent
from agents.red_team_agent import run_red_team_agent
from agents.value_alignment_agent import run_values_agent
from agents.aggregator import run_aggregator_agent
from graph.state import SynapseState

# ---------- INDIVIDUAL AGENT NODES ----------
def ethical_node(state: SynapseState):
    output = run_ethical_agent(state["user_query"])
    return {
        "agent_outputs": {
            "ethical": {"output": output}
        }
    }

def eq_node(state: SynapseState):
    output = run_eq_agent(state["user_query"])
    return {
        "agent_outputs": {
            "eq": {"output": output}
        }
    }

def risk_node(state: SynapseState):
    output = run_risk_agent(state["user_query"])
    return {
        "agent_outputs": {
            "risk": {"output": output}
        }
    }

def red_team_node(state: SynapseState):
    output = run_red_team_agent(state["user_query"])
    return {
        "agent_outputs": {
            "red_team": {"output": output}
        }
    }

def values_node(state: SynapseState):
    output = run_values_agent(state["user_query"])
    return {
        "agent_outputs": {
            "values": {"output": output}
        }
    }

# ---------- FINAL AGGREGATOR NODE ----------
def aggregator_node(state: SynapseState):
    payload = {
        "user_query": state["user_query"],
        "weights": state["weights"],
        "agent_outputs": state["agent_outputs"],
    }
    final_answer = run_aggregator_agent(payload)
    return {
        "final_answer": final_answer,
        "agent_outputs": state["agent_outputs"] 
    }