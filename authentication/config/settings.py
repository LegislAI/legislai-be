from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    secret_key: str
    refresh_secret_key: str

    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    algorithm: str

    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    timeout: int

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str


settings = Settings()
