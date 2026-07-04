from matlas.config import Settings


def test_defaults():
    settings = Settings()
    assert settings.model_hard == "claude-sonnet-5"
    assert settings.region == "US"
    assert settings.enable_web_search is False
    assert settings.web_search_max_uses == 3
    assert settings.confidence_threshold == 0.5
    assert settings.max_agent_iterations == 6


def test_env_override(monkeypatch):
    monkeypatch.setenv("MATLAS_REGION", "IN")
    monkeypatch.setenv("MATLAS_ENABLE_WEB_SEARCH", "true")
    monkeypatch.setenv("MATLAS_MAX_AGENT_ITERATIONS", "10")
    settings = Settings()
    assert settings.region == "IN"
    assert settings.enable_web_search is True
    assert settings.max_agent_iterations == 10
