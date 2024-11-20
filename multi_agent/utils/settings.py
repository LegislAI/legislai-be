from os import environ

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    langchain_tracing_v2: bool
    langchain_endpoint: str
    langchain_api_key: str
    langchain_project: str
    together_key: str


settings = Settings()
