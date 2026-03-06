"""State."""

from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import MetadataFilters


class SafeguardResult(BaseModel):
    """Safeguard result."""

    is_on_topic: bool = Field(
        ...,
        description="True if user query is about the specified topic. False otherwise.",
    )

    reason: str = Field(
        ..., description="Short reason. No sensitive data, no chain-of-thought."
    )


ContentType = Literal["text", "table_row", "table_full"]

Mode = Literal["broad", "filtered"]


class RetrievalPlan(BaseModel):
    query: str = Field(description="Cleaned retrieval query")
    ticker: Optional[str] = None
    company: Optional[str] = None
    year: Optional[str] = None
    quarter: Optional[str] = None
    content_type: Optional[ContentType] = None
    header_1: Optional[str] = None
    header_2: Optional[str] = None
    mode: Mode = "broad"


class BasicState(TypedDict):
    """BasicState."""

    user_query: str
    safeguard_result: SafeguardResult
    messages: Annotated[List, add_messages]
    answer: str


class RagState(TypedDict):
    """RagState."""

    user_query: str
    safeguard_result: SafeguardResult
    messages: Annotated[List, add_messages]
    retrieval_plan: RetrievalPlan
    metadata_filters: MetadataFilters
    retrieved_nodes: List[NodeWithScore]
    answer: str
