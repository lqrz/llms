"""Edges."""

from agent.graph.state import BasicState


def safeguard_request_router(state: BasicState):
    """Safeguard request router."""

    return state["safeguard_result"].is_on_topic
