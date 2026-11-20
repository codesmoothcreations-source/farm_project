# (settings: DB URL, JWT secret, SMTP)

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

class Settings(BaseSettings):
    APP_NAME: str
    DATABASE_URL: str
    DEBUG: bool


    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


settings = Settings()
# (settings: DB URL, JWT secret, SMTP)
