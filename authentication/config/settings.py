from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    reset_token_secret: str = "new-pass-1234"
    frontend_url: str = "http://localhost:8000"  # For reset link in email
    ses_sender_email: str = "mfranciscalemos@gmail.com"  # Verified SES email
    development_mode: bool = True
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
