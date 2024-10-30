from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    secret_key: str = ""
    refresh_secret_key: str = ""
    algorithm: str = "HS256"
    timeout: int = -1
    access_token_expire_minutes: int = -1
    refresh_token_expire_minutes: int = -1

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"  # here
