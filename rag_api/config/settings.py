from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    frontend_url: str

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str


settings = Settings()
