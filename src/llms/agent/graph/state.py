"""State."""

from typing import TypedDict, Annotated, List
from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from llama_index.core.schema import NodeWithScore


class SafeguardResult(BaseModel):
    """Safeguard result."""

    is_on_topic: bool = Field(
        ...,
        description="True if user query is about the specified topic. False otherwise.",
    )

    reason: str = Field(
        ..., description="Short reason. No sensitive data, no chain-of-thought."
    )


class BasicState(TypedDict):
    """BasicState."""

    user_query: str
    safeguard_result: SafeguardResult
    messages: Annotated[List, add_messages]
    retrieved_nodes: List[NodeWithScore]
    answer: str
