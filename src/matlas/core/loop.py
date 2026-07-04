from typing import Any

import anthropic
from pydantic import BaseModel, TypeAdapter

from matlas.config import Settings
from matlas.core.schema import EnrichedTransaction, Evidence
from matlas.core.shared_category import SharedCategory
from matlas.core.validator import validate
from matlas.core.websearch_tool import build_pause_turn_resume, web_search_tool_def
from matlas.regions.base import RegionPack

RESOLVE_MERCHANT_TOOL = {
    "name": "resolve_merchant",
    "description": (
        "Resolve the normalized merchant string to a canonical merchant, MCC, and "
        "category via the region's deterministic gazetteer/fuzzy-match resolver. "
        "Always call this before proposing a final answer."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"merchant_str": {"type": "string"}},
        "required": ["merchant_str"],
    },
}

SYSTEM_PROMPT = (
    "You are a transaction enrichment assistant. You will be given a normalized "
    "merchant string. Call resolve_merchant to get the deterministic MCC/category "
    "signal, then respond with a final JSON object matching "
    '{"merchant": str, "category": str, "confidence": float} as your final text '
    "answer. The category must be one of the matlas SharedCategory values."
)


class ProposedEnrichment(BaseModel):
    merchant: str
    category: str
    confidence: float


class EnrichmentAgent:
    def __init__(
        self,
        pack: RegionPack,
        settings: Settings,
        client: anthropic.Anthropic | None = None,
    ):
        self.pack = pack
        self.settings = settings
        self.client = client or anthropic.Anthropic()
        self.last_run_tool_calls: int | None = None

    def _tools(self) -> list[dict[str, Any]]:
        tools = [RESOLVE_MERCHANT_TOOL]
        if self.settings.enable_web_search:
            tools.append(web_search_tool_def(self.settings.web_search_max_uses))
        return tools

    def _parse_final(self, response: Any) -> ProposedEnrichment:
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        return TypeAdapter(ProposedEnrichment).validate_json(text)

    def run(self, raw: str, region: str) -> EnrichedTransaction:
        normalized = self.pack.normalize(raw)
        consistency_applicable = self.pack.consistency_applicable(normalized)
        original_user_content = normalized.merchant_str
        messages: list[dict[str, Any]] = [{"role": "user", "content": original_user_content}]

        resolved = None
        retried = False
        tool_call_count = 0

        for _ in range(self.settings.max_agent_iterations):
            response = self.client.messages.create(
                model=self.settings.model_hard,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=self._tools(),  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use" and block.name == "resolve_merchant":
                        resolved = self.pack.resolve(normalized)
                        tool_call_count += 1
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": resolved.model_dump_json(),
                            }
                        )
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                continue

            if response.stop_reason == "pause_turn":
                messages.extend(build_pause_turn_resume(original_user_content, response))
                continue

            if response.stop_reason == "end_turn":
                if resolved is None:
                    resolved = self.pack.resolve(normalized)

                proposed = self._parse_final(response)
                proposed_category = SharedCategory(proposed.category)
                verdict = validate(
                    proposed_category, proposed.confidence, resolved, consistency_applicable
                )

                if verdict.should_retry and not retried:
                    retried = True
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                f"Your proposed category was {proposed_category.value} with "
                                f"confidence {proposed.confidence}, but the resolver signal says "
                                f"{resolved.category.value} (source={resolved.source}, "
                                f"confidence={resolved.confidence}). Please reconsider and "
                                "respond again with a final JSON object."
                            ),
                        }
                    )
                    continue

                evidence = [
                    Evidence(source="llm", detail=proposed.merchant, confidence=proposed.confidence),
                    Evidence(
                        source="resolver",
                        detail=f"{resolved.source}:{resolved.mcc}",
                        confidence=resolved.confidence,
                    ),
                ]
                result = EnrichedTransaction(
                    raw=raw,
                    region=region,
                    rail=normalized.rail,
                    merchant=proposed.merchant,
                    category=verdict.final_category,
                    confidence=verdict.final_confidence,
                    consistency_check_applicable=consistency_applicable,
                    consistency_ok=(
                        (proposed_category is resolved.category) if consistency_applicable else None
                    ),
                    evidence=evidence,
                    is_unknown=verdict.final_category is SharedCategory.UNKNOWN,
                )
                self.last_run_tool_calls = tool_call_count
                return result

        self.last_run_tool_calls = tool_call_count
        return EnrichedTransaction(
            raw=raw,
            region=region,
            rail=normalized.rail,
            merchant="unknown",
            category=SharedCategory.UNKNOWN,
            confidence=0.0,
            consistency_check_applicable=consistency_applicable,
            consistency_ok=None,
            evidence=[],
            is_unknown=True,
        )
