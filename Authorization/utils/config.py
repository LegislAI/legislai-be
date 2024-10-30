from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = ""
    refresh_secret_key: str = ""
    algorithm: str = ""
    timeout: int = -1
    access_token_expire_minutes: int = -1
    refresh_token_expire_minutes: int = -1

    class Config:
        env_file = Path(Path(__file__).resolve().parent.parent) / ".env"
        extra = "ignore"


# setting = Settings()
