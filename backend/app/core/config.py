from pydantic_settings import BaseSettings
from typing import List
import json
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AutoStream AI Infinity"
    DEBUG: bool = False
    SECRET_KEY: str = "changethissecretkey"
    ALLOWED_ORIGINS: str = '["http://localhost:5173"]'

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://autostream:supersecretpassword@localhost:5432/autostream_db"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security
    FERNET_KEY: str = ""

    # Google / Gemini
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/accounts/oauth/google/callback")

    # Meta
    META_CLIENT_ID: str = ""
    META_CLIENT_SECRET: str = ""
    META_REDIRECT_URI: str = os.getenv("META_REDIRECT_URI", "http://localhost:8000/api/v1/accounts/oauth/meta/callback")
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_WEBHOOK_VERIFY_TOKEN: str = ""
    # Comma-separated permissions requested during Meta OAuth.
    # Keep minimal for local dev; add more only after enabling permissions in Meta console.
    META_SCOPES: str = "public_profile,pages_show_list"

    # Google Drive (For Instagram Public URLs)
    GOOGLE_DRIVE_PUBLIC_FOLDER_ID: str = ""

    # If true, after a successful publish the system will attempt to delete the
    # original source video from Google Drive (requires Drive scope).
    DELETE_SOURCE_DRIVE_FILE_AFTER_PUBLISH: bool = False

    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    @property
    def allowed_origins_list(self) -> List[str]:
        try:
            origins = json.loads(self.ALLOWED_ORIGINS)
        except Exception:
            origins = []
        # Always ensure localhost dev origins are present
        defaults = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
        for d in defaults:
            if d not in origins:
                origins.append(d)
        return origins

    class Config:
        env_file = ".env"
        case_sensitive = True

    def model_post_init(self, __context) -> None:
        if not self.META_CLIENT_ID and self.META_APP_ID:
            self.META_CLIENT_ID = self.META_APP_ID
        if not self.META_CLIENT_SECRET and self.META_APP_SECRET:
            self.META_CLIENT_SECRET = self.META_APP_SECRET


settings = Settings()
