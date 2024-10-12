from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = None
    refresh_secret_key: str = None
    algorithm: str = None
    timeout: int = None
    access_token_expire_minutes: int = None
    refresh_token_expire_minutes: int = None

    class Config:
        env_file = Path(Path(__file__).resolve().parent.parent) / ".env"
        extra = "ignore"


setting = Settings()
