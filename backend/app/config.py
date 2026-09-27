from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./csa.db"
    OPENAI_API_KEY: Optional[str] = None
    PYANNOTE_AUTH_TOKEN: Optional[str] = None
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    WHISPER_MODEL: str = "base"

    class Config:
        env_file = ".env"


settings = Settings()
