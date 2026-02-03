"""State."""

from typing import TypedDict, Annotated, List
from langgraph.graph import add_messages


class BasicState(TypedDict):
    """BasicState."""

    is_safe_request: bool
    messages: Annotated[List, add_messages]
