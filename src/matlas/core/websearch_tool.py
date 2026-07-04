from typing import Any


def web_search_tool_def(max_uses: int) -> dict[str, Any]:
    return {"type": "web_search_20260209", "name": "web_search", "max_uses": max_uses}


def build_pause_turn_resume(original_user_content: Any, response: Any) -> list[dict[str, Any]]:
    """Server-side web search hit its internal cap (stop_reason == "pause_turn").
    Resume by resending the original user turn + the paused assistant response
    verbatim — no synthetic "Continue" message."""
    return [
        {"role": "user", "content": original_user_content},
        {"role": "assistant", "content": response.content},
    ]
