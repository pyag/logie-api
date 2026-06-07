from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str
    cors_origin: str
    db_url: str
    secret_key: str
    jwt_secret: str
    jwt_exp_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
