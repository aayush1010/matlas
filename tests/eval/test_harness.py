from types import SimpleNamespace

from matlas.core.shared_category import SharedCategory
from matlas.eval.gold import GoldRow
from matlas.eval.harness import run_benchmark


class _FakeAgent:
    """Replays canned right/wrong predictions instead of calling a real model."""

    def __init__(self, predictions, tool_calls=None):
        self._predictions = predictions
        self.last_run_tool_calls = None
        self._tool_calls = tool_calls

    def run(self, raw, region):
        merchant, category = self._predictions[raw]
        if self._tool_calls is not None:
            self.last_run_tool_calls = self._tool_calls[raw]
        return SimpleNamespace(merchant=merchant, category=category)


def test_accuracy_computation_against_known_right_and_wrong_predictions():
    gold_rows = [
        GoldRow(raw="starbucks", merchant="Starbucks", category="food_and_drink", mcc="5814"),
        GoldRow(raw="target", merchant="Target", category="general_merchandise", mcc="5310"),
    ]
    agent = _FakeAgent(
        {
            "starbucks": ("Starbucks", SharedCategory.FOOD_AND_DRINK),
            "target": ("Wrong Merchant", SharedCategory.MEDICAL),
        }
    )
    result = run_benchmark(agent, gold_rows)
    assert result.n == 2
    assert result.merchant_accuracy == 0.5
    assert result.category_accuracy == 0.5
    assert result.mean_tool_calls is None


def test_mean_tool_calls_averaged_when_agent_exposes_it():
    gold_rows = [
        GoldRow(raw="starbucks", merchant="Starbucks", category="food_and_drink", mcc="5814"),
        GoldRow(raw="target", merchant="Target", category="general_merchandise", mcc="5310"),
    ]
    agent = _FakeAgent(
        {
            "starbucks": ("Starbucks", SharedCategory.FOOD_AND_DRINK),
            "target": ("Target", SharedCategory.GENERAL_MERCHANDISE),
        },
        tool_calls={"starbucks": 1, "target": 3},
    )
    result = run_benchmark(agent, gold_rows)
    assert result.merchant_accuracy == 1.0
    assert result.mean_tool_calls == 2.0
