import json
from typing import Any
import xml.etree.ElementTree as ET

from google.genai import types

from schemas.diagram_schema import DiagramResponse
from services.gemini_service import GeminiService
from utils.logger import get_logger

logger = get_logger(__name__)


class DiagramService:
    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service or GeminiService()
        self._generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=DiagramResponse.model_json_schema(),
            max_output_tokens=4096,
            temperature=0.2,
            top_p=0.8,
        )

    def generate_structure(self, text: str) -> DiagramResponse:
        prompt = (
            "Eres un generador de procesos BPMN.\n"
            "Convierte el siguiente texto en una estructura JSON editable para Spring Boot.\n"
            "Devuelve SOLO JSON válido, sin markdown, sin explicación y sin XML.\n"
            "La estructura debe incluir:\n"
            "- processName: nombre del proceso.\n"
            "- areas: lista de áreas o lanes.\n"
            "- tasks: lista de tareas con id, name, area y type.\n"
            "- gateways: lista de decisiones con id, name, type.\n"
            "- flows: conexiones con from, to, condition opcional y label opcional.\n\n"
            "Reglas:\n"
            "- Usa ids cortos y consistentes como t1, g1, f1.\n"
            "- Toda tarea debe modelarse como type: userTask. No uses task, serviceTask, manualTask ni otros tipos para tareas normales.\n"
            "- Si el texto no especifica un tipo especial, siempre usa userTask.\n"
            "- Si hay decisiones, usa exclusive por defecto.\n"
            "- Conecta start -> primera tarea -> gateways -> siguientes tareas -> end.\n"
            "- Si el texto menciona áreas, inclúyelas como lanes/areas.\n"
            "- Si falta información, infiere la mínima estructura coherente.\n"
            "- No mezcles ids entre nodos: cada task, gateway y flow debe tener su propio id estable.\n"
            "- Si reaparece una misma entidad, conserva el mismo id para evitar cambios innecesarios al editar luego.\n\n"
            "Formato esperado:\n"
            '{\n'
            '  "processName": "Proceso de compra",\n'
            '  "areas": ["Ventas", "Gerencia", "Facturación"],\n'
            '  "tasks": [{"id": "t1", "name": "Registrar solicitud", "area": "Ventas", "type": "userTask"}],\n'
            '  "gateways": [{"id": "g1", "name": "¿Monto mayor a 1000?", "type": "exclusive"}],\n'
            '  "flows": [{"from": "start", "to": "t1"}]\n'
            '}\n\n'
            f"Texto: {text.strip()}"
        )

        raw_response = self._gemini_service.generate_text(prompt, config=self._generation_config)
        logger.info("Gemini diagram response received: %s", raw_response[:200])
        payload = self._parse_json(raw_response)
        self._validate_payload(payload)
        return DiagramResponse.model_validate(payload)

    def _parse_json(self, raw_response: str) -> dict[str, Any]:
        cleaned = self._clean_response(raw_response)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.exception("Diagram response is not valid JSON")
            raise ValueError("Gemini no devolvió JSON válido para el diagrama") from exc

        if not isinstance(parsed, dict):
            raise ValueError("La respuesta del diagrama debe ser un objeto JSON")

        return parsed

    def _clean_response(self, raw_response: str) -> str:
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

        return cleaned

    def _validate_payload(self, payload: dict[str, Any]) -> None:
        tasks = payload.get("tasks") or []
        gateways = payload.get("gateways") or []
        flows = payload.get("flows") or []
        areas = payload.get("areas") or []

        if not isinstance(tasks, list) or not isinstance(gateways, list) or not isinstance(flows, list) or not isinstance(areas, list):
            raise ValueError("La estructura del diagrama no tiene listas validas")

        for task in tasks:
            if isinstance(task, dict):
                task["type"] = "userTask"
