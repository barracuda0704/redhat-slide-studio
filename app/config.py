from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_TITLE: str = "Slide Studio"
    DATA_DIR: str = "/app/data"
    ADMIN_EMAIL: str = "barracuda0704@gmail.com"
    ADMIN_INITIAL_PASSWORD: str = "***REMOVED***"
    SESSION_COOKIE_NAME: str = "session_token"
    SESSION_TTL_DAYS: int = 7
    SESSION_COOKIE_SECURE: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
