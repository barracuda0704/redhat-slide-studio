import os
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
    MAX_OUTPUT_TOKENS: int = 32000

    # Image generation shells out to the locally-installed `cursor-agent` CLI
    # (its cursor.GenerateImage tool) rather than Vertex AI Imagen/Gemini —
    # every image model on this GCP project is blocked by the org's
    # constraints/vertexai.allowedModels policy. Only works when the app
    # runs natively on a machine with a logged-in cursor-agent session (this
    # is why the app was moved off Docker onto a native launchd service).
    CURSOR_AGENT_MODEL: str = "claude-sonnet-5-medium"
    # Cursor's backend has shown sustained resource_exhausted errors on
    # heavier-demand models (Claude, Grok) while lighter models kept working
    # throughout — falls back to this one rather than failing outright.
    CURSOR_AGENT_FALLBACK_MODEL: str = "gpt-5.4-mini-low"
    CURSOR_AGENT_TIMEOUT_SECONDS: int = 120

    ADMIN_EMAIL: str = "barracuda0704@gmail.com"
    ADMIN_INITIAL_PASSWORD: str = "***REMOVED***"
    SESSION_COOKIE_NAME: str = "session_token"
    SESSION_TTL_DAYS: int = 7
    SESSION_COOKIE_SECURE: bool = False
    LOGIN_DISABLED: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


# Unsplash API key: stored as its own file under DATA_DIR (not the process
# .env) so it can be registered/cleared at runtime without needing a
# restart to pick up a changed pydantic Settings value.
def _unsplash_key_path() -> Path:
    return Path(settings.DATA_DIR) / "unsplash_key.txt"


def get_unsplash_key() -> str:
    p = _unsplash_key_path()
    return p.read_text("utf-8").strip() if p.exists() else ""


def save_unsplash_key(key: str) -> None:
    p = _unsplash_key_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(key.strip(), encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


def clear_unsplash_key() -> None:
    p = _unsplash_key_path()
    if p.exists():
        p.unlink()
