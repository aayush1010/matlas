from pydantic import BaseModel

from matlas.core.shared_category import SharedCategory
from matlas.regions.base import ResolvedSignal

HIGH_RESOLVER_CONFIDENCE = 0.85


class ValidationResult(BaseModel):
    final_category: SharedCategory
    final_confidence: float
    should_retry: bool


def validate(
    proposed_category: SharedCategory,
    proposed_confidence: float,
    resolved: ResolvedSignal,
    consistency_applicable: bool,
) -> ValidationResult:
    if not consistency_applicable:
        return ValidationResult(
            final_category=proposed_category,
            final_confidence=proposed_confidence,
            should_retry=False,
        )

    if proposed_category is resolved.category:
        return ValidationResult(
            final_category=proposed_category,
            final_confidence=(proposed_confidence + resolved.confidence) / 2,
            should_retry=False,
        )

    if resolved.confidence >= HIGH_RESOLVER_CONFIDENCE:
        return ValidationResult(
            final_category=resolved.category,
            final_confidence=resolved.confidence * 0.5,
            should_retry=True,
        )

    return ValidationResult(
        final_category=proposed_category,
        final_confidence=proposed_confidence * 0.5,
        should_retry=False,
    )
