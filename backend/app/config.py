import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    data_dir: str = os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def ensure_data_dir() -> Path:
    p = Path(settings.data_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "uploads").mkdir(exist_ok=True)
    (p / "refined").mkdir(exist_ok=True)
    (p / "db").mkdir(exist_ok=True)
    (p / "docs").mkdir(exist_ok=True)
    return p
