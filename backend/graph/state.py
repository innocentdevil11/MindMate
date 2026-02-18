from typing import TypedDict, Dict, Any, Annotated
from operator import add

def merge_agent_outputs(left: Dict[str, Dict[str, Any]], right: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Merge agent outputs from parallel nodes."""
    return {**left, **right}

class SynapseState(TypedDict):
    # User input
    user_query: str
    # User-controlled weights
    weights: Dict[str, float]
    # Outputs from individual agents - with reducer for parallel updates
    agent_outputs: Annotated[Dict[str, Dict[str, Any]], merge_agent_outputs]
    # Final decision
    final_answer: str