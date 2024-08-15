from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    stripe_api_key: str
    stripe_pub_key: str
    stripe_signing_secret: str


settings = Settings()
