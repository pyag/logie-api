from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str
    cors_origin: str
    db_url: str
    secret_key: str
    jwt_secret: str
    jwt_exp_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env")
