import json
from typing import Any

from schemas.diagram_schema import DiagramResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class DiagramService:
    def __init__(self, gemini_service: object | None = None) -> None:
        if gemini_service is not None:
            self._gemini_service = gemini_service
        else:
            from services.gemini_service import GeminiService

            self._gemini_service = GeminiService()

    def generate_structure(self, text: str) -> DiagramResponse:
        prompt = (
            "Devuelve una estructura JSON con tasks, flows y areas a partir del siguiente proceso. "
            "Responde solo con JSON válido, sin markdown ni explicaciones. "
            f"Proceso: {text.strip()}"
        )

        raw_response = self._gemini_service.generate_text(prompt)
        logger.info("Gemini diagram response received: %s", raw_response[:200])

        payload = self._parse_json(raw_response)
        return DiagramResponse.model_validate(payload)

    def _parse_json(self, raw_response: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            logger.exception("Diagram response is not valid JSON")
            raise ValueError("Gemini no devolvió JSON válido para el diagrama") from exc

        if not isinstance(parsed, dict):
            raise ValueError("La respuesta del diagrama debe ser un objeto JSON")

        return parsed
