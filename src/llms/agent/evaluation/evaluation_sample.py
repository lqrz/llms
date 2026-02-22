"""EvaluationSample."""

from dataclasses import dataclass
from typing import List, Dict, Any
import re


@dataclass
class EvaluationSample:
    """EvaluationSample."""

    id: int
    query: str
    source_docs: List[str]
    question_type: str
    source_chunk_type: str
    answer: str

    @classmethod
    def from_row(cls, row: Dict[str, Any], company_files: Dict[str, List[str]]):
        obj = cls(**row)
        pattern = r"\*([A-Za-z0-9_.-]+)\*"
        m = re.search(pattern, str(obj.source_docs))
        ticker = m.group(1) if m else None
        if ticker is not None and ticker in company_files:
            obj.source_docs = company_files[ticker]
        return obj
