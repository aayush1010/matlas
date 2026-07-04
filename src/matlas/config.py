from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "MATLAS_"}

    model_hard: str = "claude-sonnet-5"
    model_cheap: str = "claude-haiku-4-5-20251001"
    judge_model: str = "claude-sonnet-5"
    region: str = "US"
    taxonomy: str = "plaid_pfc"
    enable_web_search: bool = False
    web_search_max_uses: int = 3
    confidence_threshold: float = 0.5
    max_agent_iterations: int = 6
