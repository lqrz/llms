"""InvokeRequest."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class InvokeRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
