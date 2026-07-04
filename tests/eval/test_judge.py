from types import SimpleNamespace
from unittest.mock import MagicMock

from matlas.eval.judge import exact_match_judge, llm_judge, make_llm_judge


def test_exact_match_judge_case_and_whitespace_insensitive():
    assert exact_match_judge("  Starbucks ", "starbucks")
    assert not exact_match_judge("Starbucks", "Blue Bottle Coffee")


def _fake_client(answer: str) -> MagicMock:
    client = MagicMock()
    client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=answer)]
    )
    return client


def test_llm_judge_yes():
    client = _fake_client("yes")
    assert llm_judge("Blue Bottle", "Blue Bottle Coffee", client, "claude-haiku-4-5-20251001")


def test_llm_judge_no():
    client = _fake_client("no")
    assert not llm_judge("Starbucks", "Dunkin", client, "claude-haiku-4-5-20251001")


def test_make_llm_judge_returns_callable_matching_run_benchmark_signature():
    client = _fake_client("yes")
    judge = make_llm_judge(client, "claude-haiku-4-5-20251001")
    assert judge("Blue Bottle", "Blue Bottle Coffee") is True
