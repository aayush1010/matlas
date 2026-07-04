from typing import Literal

from pydantic import BaseModel

from matlas.core.shared_category import SharedCategory


class Evidence(BaseModel):
    source: Literal["llm", "resolver", "gazetteer", "web_search"]
    detail: str
    confidence: float


class EnrichedTransaction(BaseModel):
    raw: str
    region: str
    rail: str
    merchant: str
    category: SharedCategory
    confidence: float
    consistency_check_applicable: bool
    consistency_ok: bool | None
    evidence: list[Evidence]
    is_unknown: bool
