from functools import lru_cache

from core.config import Settings, get_settings


def get_app_settings() -> Settings:
    return get_settings()


@lru_cache
def get_gemini_service():
    from services.gemini_service import GeminiService

    return GeminiService()
