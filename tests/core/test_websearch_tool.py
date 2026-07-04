from types import SimpleNamespace

from matlas.core.websearch_tool import build_pause_turn_resume, web_search_tool_def


def test_web_search_tool_def_shape():
    tool = web_search_tool_def(max_uses=3)
    assert tool == {"type": "web_search_20260209", "name": "web_search", "max_uses": 3}


def test_build_pause_turn_resume_resends_user_and_assistant_content():
    response = SimpleNamespace(content=[{"type": "text", "text": "partial"}], stop_reason="pause_turn")
    messages = build_pause_turn_resume("original descriptor", response)
    assert messages == [
        {"role": "user", "content": "original descriptor"},
        {"role": "assistant", "content": response.content},
    ]
