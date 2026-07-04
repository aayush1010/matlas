from functools import partial
from typing import Callable

from anthropic import Anthropic


def exact_match_judge(predicted: str, expected: str) -> bool:
    # ponytail: exact-match only for Week 1 — gold set has unambiguous canonical
    # names. Upgrade to an LLM-based fuzzy judge if/when the gold set grows messier.
    return predicted.strip().lower() == expected.strip().lower()


def llm_judge(predicted: str, expected: str, client: Anthropic, model: str) -> bool:
    """Fuzzy same-merchant judge for gold sets messier than exact match can
    handle (e.g. 'Blue Bottle' vs 'Blue Bottle Coffee'). One-turn yes/no,
    cheap model, no tools, no retries."""
    response = client.messages.create(
        model=model,
        max_tokens=5,
        messages=[
            {
                "role": "user",
                "content": (
                    f'Are "{predicted}" and "{expected}" the same real-world merchant '
                    'or company? Answer only "yes" or "no".'
                ),
            }
        ],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return text.strip().lower().startswith("yes")


def make_llm_judge(client: Anthropic, model: str) -> Callable[[str, str], bool]:
    return partial(llm_judge, client=client, model=model)
