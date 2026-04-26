from functools import lru_cache
from os import getenv

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    gemini_api_key: str = Field(default_factory=lambda: getenv("GEMINI_API_KEY", ""))
    gemini_model: str = Field(default_factory=lambda: getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    gemini_model_fallbacks: list[str] = Field(
        default_factory=lambda: [
            model.strip()
            for model in getenv("GEMINI_MODEL_FALLBACKS", "gemini-2.0-flash,gemini-1.5-flash").split(",")
            if model.strip()
        ]
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY no está configurada.")
    return settings
