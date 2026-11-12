from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

env_file=Path(__file__).resolve().parent.parent / ".env",

class Settings(BaseSettings):
    APP_NAME:str = "My API"
    DATABASE_URL:str = ""
    OPENAI_API_KEY:str = ""
    ANTHROPIC_API_KEY:str = ""
    EXTRACTION_MODEL:str = ""

    model_config = SettingsConfigDict(
        env_file=env_file,
        extra="ignore",
        env_file_encoding = "utf-8"
    )



@lru_cache
def get_settings()->Settings:
    return Settings()

settings = get_settings()