from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_TITLE: str = "Slide Studio"
    DATA_DIR: str = "/app/data"
    ENGINE_DIR: str = str(BASE_DIR / "engine")

    USE_VERTEX: bool = True
    VERTEX_PROJECT_ID: str = ""
    VERTEX_REGION: str = "us-east5"
    ANTHROPIC_API_KEY: str = ""
    MODEL_NAME: str = "claude-opus-4-6"
    MAX_OUTPUT_TOKENS: int = 16384

    ADMIN_EMAIL: str = "barracuda0704@gmail.com"
    ADMIN_INITIAL_PASSWORD: str = "***REMOVED***"
    SESSION_COOKIE_NAME: str = "session_token"
    SESSION_TTL_DAYS: int = 7
    SESSION_COOKIE_SECURE: bool = False
    LOGIN_DISABLED: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
