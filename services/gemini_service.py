from functools import lru_cache
import time

from core.config import get_settings


class GeminiService:
    def __init__(self) -> None:
        settings = get_settings()
        self._model_name = settings.gemini_model
        self._fallback_models = [
            model for model in settings.gemini_model_fallbacks if model and model != self._model_name
        ]

        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY no está configurada.")

        try:
            from google import genai
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Falta instalar el cliente oficial de Gemini (google-genai) en el entorno virtual de system-ai."
            ) from exc

        self._client = genai.Client(api_key=settings.gemini_api_key)

    def generate_text(self, prompt: str) -> str:
        return self.generate_text_with_attempts(prompt)[0]

    def generate_text_with_attempts(self, prompt: str) -> tuple[str, int]:
        candidates = [self._model_name, *self._fallback_models]
        last_exception: Exception | None = None

        for attempt, model_name in enumerate(candidates, start=1):
            try:
                return self._generate_once(prompt, model_name), attempt
            except Exception as exc:
                last_exception = exc
                if self._is_retryable_quota_error(exc):
                    time.sleep(self._retry_delay_seconds(exc))
                    try:
                        return self._generate_once(prompt, model_name), attempt
                    except Exception as retry_exc:
                        last_exception = retry_exc
                        continue

        if last_exception is not None:
            raise last_exception
        raise RuntimeError("No se pudo generar texto con Gemini.")

    def _generate_once(self, prompt: str, model_name: str) -> str:
        response = self._client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini no devolvió texto.")
        return text.strip()

    def _is_retryable_quota_error(self, exc: Exception) -> bool:
        error_name = exc.__class__.__name__
        message = str(exc).lower()
        return error_name in {"ServerError", "ClientError"} and (
            "503" in message
            or "429" in message
            or "unavailable" in message
            or "high demand" in message
            or "resource_exhausted" in message
            or "quota exceeded" in message
        )

    def _retry_delay_seconds(self, exc: Exception) -> float:
        message = str(exc).lower()
        marker = "retry in "
        if marker in message:
            fragment = message.split(marker, 1)[1]
            digits: list[str] = []
            for char in fragment:
                if char.isdigit() or char == ".":
                    digits.append(char)
                else:
                    break
            try:
                value = float("".join(digits))
                if value > 0:
                    return min(value, 5.0)
            except ValueError:
                pass
        return 1.5


@lru_cache
def get_default_gemini_service() -> GeminiService:
    return GeminiService()
