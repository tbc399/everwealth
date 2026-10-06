from pydantic import HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    auth_token_secret: str | None = None
    plaid_client_id: str
    plaid_secret: str
    plaid_env: str = "sandbox"
    plaid_webhook_handler_url: HttpUrl
    app_name: str = "Everwealth"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "no-reply@everwealth.local"
    smtp_use_tls: bool = True


settings = Settings()
