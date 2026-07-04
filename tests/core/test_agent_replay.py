from types import SimpleNamespace
from unittest.mock import MagicMock

from matlas.config import Settings
from matlas.core.loop import EnrichmentAgent
from matlas.core.shared_category import SharedCategory
from matlas.regions.us import USRegionPack

RAW = "SQ *STARBUCKS #4521 SEATTLE WA"


def _tool_use_response(tool_use_id="t1", merchant_str="STARBUCKS"):
    block = SimpleNamespace(
        type="tool_use", id=tool_use_id, name="resolve_merchant", input={"merchant_str": merchant_str}
    )
    return SimpleNamespace(stop_reason="tool_use", content=[block])


def _end_turn_response(merchant, category, confidence, fenced=False):
    text = (
        f'{{"merchant": "{merchant}", "category": "{category.value}", '
        f'"confidence": {confidence}}}'
    )
    if fenced:
        text = f"```json\n{text}\n```"
    block = SimpleNamespace(type="text", text=text)
    return SimpleNamespace(stop_reason="end_turn", content=[block])


def _pause_turn_response():
    block = SimpleNamespace(type="text", text="")
    return SimpleNamespace(stop_reason="pause_turn", content=[block])


def _agent(responses, max_agent_iterations=6):
    client = MagicMock()
    client.messages.create.side_effect = responses
    settings = Settings(max_agent_iterations=max_agent_iterations)
    return EnrichmentAgent(USRegionPack(), settings, client=client)


def test_straightforward_agreement():
    responses = [
        _tool_use_response(),
        _end_turn_response("Starbucks", SharedCategory.FOOD_AND_DRINK, 0.9),
    ]
    agent = _agent(responses)
    result = agent.run(RAW, "US")
    assert result.category is SharedCategory.FOOD_AND_DRINK
    assert result.consistency_ok is True
    assert result.is_unknown is False


def test_final_answer_wrapped_in_markdown_fence_still_parses():
    responses = [
        _tool_use_response(),
        _end_turn_response("Starbucks", SharedCategory.FOOD_AND_DRINK, 0.9, fenced=True),
    ]
    agent = _agent(responses)
    result = agent.run(RAW, "US")
    assert result.category is SharedCategory.FOOD_AND_DRINK
    assert result.is_unknown is False


def test_contradiction_triggers_self_correction_then_agrees():
    responses = [
        _tool_use_response(),
        _end_turn_response("Starbucks", SharedCategory.GENERAL_MERCHANDISE, 0.8),
        _end_turn_response("Starbucks", SharedCategory.FOOD_AND_DRINK, 0.9),
    ]
    agent = _agent(responses)
    result = agent.run(RAW, "US")
    assert result.category is SharedCategory.FOOD_AND_DRINK
    assert result.consistency_ok is True
    assert agent.client.messages.create.call_count == 3


def test_pause_turn_resume_then_completes():
    responses = [
        _pause_turn_response(),
        _tool_use_response(),
        _end_turn_response("Starbucks", SharedCategory.FOOD_AND_DRINK, 0.9),
    ]
    agent = _agent(responses)
    result = agent.run(RAW, "US")
    assert result.category is SharedCategory.FOOD_AND_DRINK
    assert agent.client.messages.create.call_count == 3


def test_unknown_merchant():
    responses = [
        _tool_use_response(merchant_str="TOTALLY UNKNOWN MERCHANT XYZ"),
        _end_turn_response("Totally Unknown Merchant Xyz", SharedCategory.UNKNOWN, 0.1),
    ]
    agent = _agent(responses)
    result = agent.run("TOTALLY UNKNOWN MERCHANT XYZ", "US")
    assert result.category is SharedCategory.UNKNOWN
    assert result.is_unknown is True


def test_iteration_budget_exhausted_returns_unknown_not_exception():
    responses = [_tool_use_response() for _ in range(3)]
    agent = _agent(responses, max_agent_iterations=3)
    result = agent.run(RAW, "US")
    assert result.category is SharedCategory.UNKNOWN
    assert result.confidence == 0.0
    assert result.is_unknown is True
