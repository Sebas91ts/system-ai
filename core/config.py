from functools import lru_cache
from os import getenv

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    gemini_api_keys: list[str] = Field(
        default_factory=lambda: [
            key.strip()
            for key in getenv("GEMINI_API_KEYS", getenv("GEMINI_API_KEY", "")).split(",")
            if key.strip()
        ]
    )
    gemini_model: str = Field(default_factory=lambda: getenv("GEMINI_MODEL", ""))
    gemini_model_fallbacks: list[str] = Field(
        default_factory=lambda: [
            model.strip()
            for model in getenv("GEMINI_MODEL_FALLBACKS", "").split(",")
            if model.strip()
        ]
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.gemini_api_keys:
        raise ValueError("No hay claves de Gemini configuradas. Define GEMINI_API_KEY o GEMINI_API_KEYS.")
    return settings
