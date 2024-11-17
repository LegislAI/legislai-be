from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    frontend_url: str
    ses_sender_email: str

    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str

    stripe_api_key: str


settings = Settings()
