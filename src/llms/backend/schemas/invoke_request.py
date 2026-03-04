"""InvokeRequest."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal


class WorkflowKwargs(BaseModel):
    """Workflow kwargs."""

    collection_name: str
    alpha: float
    top_k_each: int
    top_k_final: int


class InvokeRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    workflow_type: Literal["basic", "rag"]
    workflow_kwargs: WorkflowKwargs
    metadata: Dict[str, Any] = Field(default_factory=dict)
