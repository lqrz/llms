"""Basic agent."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from src.agent.state import BasicState
from src.agent.nodes import (
    safeguard_request,
    safeguard_request_reject,
    generate_response,
)
from src.agent.edges import safeguard_request_router


checkpointer = InMemorySaver()


def build_basic_graph():
    """Build basic graph."""
    workflow = StateGraph(BasicState)
    workflow.add_node("safeguard_request", safeguard_request)
    workflow.add_node("safeguard_request_reject", safeguard_request_reject)
    workflow.add_node("generate_response", generate_response)
    workflow.add_conditional_edges(
        "safeguard_request",
        safeguard_request_router,
        {
            True: "generate_response",
            False: "safeguard_request_reject",
        },
    )
    workflow.add_edge("safeguard_request_reject", END)
    workflow.add_edge("generate_response", END)
    workflow.set_entry_point("safeguard_request")

    # with short term memory
    return workflow.compile(checkpointer=checkpointer)

    # without short term memory
    # return workflow.compile()
