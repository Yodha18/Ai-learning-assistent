from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./ai_learning.db"  # Default to SQLite for easier testing
    SECRET_KEY: str = "dev-secret-key"
    GEMINI_API_KEY: str = ""
    GEMINI_CHAT_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    SERPAPI_API_KEY: str = ""
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 20
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/api/auth/google/callback"
    APP_BASE_URL: str = "http://127.0.0.1:8000"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    @property
    def ai_configured(self) -> bool:
        """Whether an actual Gemini API key is available."""
        key = (self.GEMINI_API_KEY or "").strip()
        return bool(key and "your_" not in key.lower() and not key.startswith("replace"))

    @property
    def gemini_configured(self) -> bool:
        return self.ai_configured


settings = Settings()
