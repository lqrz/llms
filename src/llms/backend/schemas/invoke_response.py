"""InvokeResponse."""

from pydantic import BaseModel, Field
from typing import Dict, Any, Union


class InvokeResponse(BaseModel):
    thread_id: Union[str, int]
    answer: str
    raw: Dict[str, Any] = Field(default_factory=dict)
