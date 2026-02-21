"""Basic agent."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from llms.agent.graph.state import BasicState
from llms.agent.graph.nodes import (
    safeguard_request,
    safeguard_request_reject,
    generate_response,
)
from llms.agent.graph.edges import safeguard_request_router


checkpointer = InMemorySaver()


def build_basic_graph(is_use_short_term_memory: bool = True):
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

    # short term memory
    checkpointer = checkpointer if is_use_short_term_memory else None

    return workflow.compile(checkpointer=checkpointer)
