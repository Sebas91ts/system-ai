from functools import lru_cache
from typing import Any

from core.config import get_settings


class GeminiService:
    def __init__(self) -> None:
        settings = get_settings()

        self._api_keys = settings.gemini_api_keys
        self._model_name = settings.gemini_model
        self._fallback_models = [
            model for model in settings.gemini_model_fallbacks if model and model != self._model_name
        ]

        try:
            from google import genai
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Falta instalar el cliente oficial de Gemini (google-genai) en el entorno virtual de system-ai."
            ) from exc

        self._client_factory = genai.Client

    def generate_text(self, prompt: str, config: Any | None = None) -> str:
        return self.generate_text_with_attempts(prompt, config=config)[0]

    def generate_text_with_attempts(self, prompt: str, config: Any | None = None) -> tuple[str, int]:
        candidates = [self._model_name, *self._fallback_models]
        api_key = self._api_keys[0]
        masked_key = self._mask_api_key(api_key)
        client = self._client_factory(api_key=api_key)

        for attempt, model_name in enumerate(candidates, start=1):
            try:
                print(
                    f"[GeminiService] Intento con key {masked_key} y modelo '{model_name}'"
                )
                return self._generate_once(client, prompt, model_name, config=config), attempt
            except Exception as exc:
                print(
                    f"[GeminiService] Fallo con key {masked_key} y modelo '{model_name}': "
                    f"{exc.__class__.__name__} -> {exc}"
                )
                if self._is_resource_exhausted_error(exc):
                    raise exc

        raise RuntimeError("No se pudo generar texto con Gemini.")

    def _generate_once(self, client: Any, prompt: str, model_name: str, config: Any | None = None) -> str:
        kwargs: dict[str, Any] = {
            "model": model_name,
            "contents": prompt,
        }
        if config is not None:
            kwargs["config"] = config

        response = client.models.generate_content(**kwargs)
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini no devolvio texto.")
        return text.strip()

    def _is_resource_exhausted_error(self, exc: Exception) -> bool:
        error_name = exc.__class__.__name__
        message = str(exc).lower()
        return error_name in {"ServerError", "ClientError"} and (
            "resource_exhausted" in message
            or "quota exceeded" in message
            or "429" in message
        )

    def _mask_api_key(self, api_key: str) -> str:
        if not api_key:
            return "sin-clave"

        if len(api_key) <= 8:
            return "***"

        return f"{api_key[:4]}...{api_key[-4:]}"


@lru_cache
def get_default_gemini_service() -> GeminiService:
    return GeminiService()
