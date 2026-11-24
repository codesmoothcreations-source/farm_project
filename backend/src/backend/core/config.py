# (settings: DB URL, JWT secret, SMTP)

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Farm Project"
    DATABASE_URL: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/farm_project'
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore',
    )


settings = Settings()
# (settings: DB URL, JWT secret, SMTP)
