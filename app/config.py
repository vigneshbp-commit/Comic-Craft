from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
STATIC_DIR = APP_DIR / "static"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"
TEMPLATES_DIR = APP_DIR / "templates"


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "ComicCraft"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # AI Configurations
    GEMINI_API_KEY: str = ""
    HF_API_KEY: str = ""
    IMAGE_GEN_BACKEND: str = "auto"
    DEFAULT_MODEL_FLASH: str = "models/gemini-3.8-flash"
    DEFAULT_MODEL_PRO: str = "models/gemini-3.5-flash"
    SD_MODEL_ID: str = "stabilityai/stable-diffusion-3-medium-diffusers"
    IMAGE_GEN_TIMEOUT: int = 60
    POLLINATIONS_ENABLED: bool = True


settings = Settings()

# Ensure directories exist
PANELS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "images").mkdir(parents=True, exist_ok=True)
