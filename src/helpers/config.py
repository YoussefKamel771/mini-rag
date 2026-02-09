from pydantic_settings import BaseSettings , SettingsConfigDict
from typing import List

class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str

    # Add these two lines:
    FILE_ALLOWED_TYPES: List[str]
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    # model_config = SettingsConfigDict(env_file=".env")
    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
