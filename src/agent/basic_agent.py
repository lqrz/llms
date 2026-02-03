"""Basic agent."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from src.agent.state import BasicState
from src.agent.nodes import generate_response


checkpointer = InMemorySaver()


def build_basic_graph():
    """Build basic graph."""
    workflow = StateGraph(BasicState)
    workflow.add_node("generate_response", generate_response)
    workflow.add_edge("generate_response", END)
    workflow.set_entry_point("generate_response")

    # with short term memory
    return workflow.compile(checkpointer=checkpointer)

    # without short term memory
    # return workflow.compile()
