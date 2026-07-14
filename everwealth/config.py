from pydantic_settings import BaseSettings
from pydantic import HttpUrl


class Settings(BaseSettings):
    database_url: str
    plaid_client_id: str
    plaid_secret: str
    plaid_env: str
    plaid_webhook_handler_url:  HttpUrl


settings = Settings()
