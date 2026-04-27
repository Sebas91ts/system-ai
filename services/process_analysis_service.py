import json
from typing import Any

from schemas.process_analysis_schema import ProcessAnalysisRequest, ProcessAnalysisResponse
from services.gemini_service import GeminiService
from utils.logger import get_logger

logger = get_logger(__name__)


class ProcessAnalysisService:
    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service or GeminiService()

    def analyze_process(self, payload: ProcessAnalysisRequest) -> ProcessAnalysisResponse:
        prompt = self._build_prompt(payload)
        raw_response = self._gemini_service.generate_text(prompt)
        logger.info("Gemini process analysis response received: %s", raw_response[:220])
        parsed = self._parse_json(raw_response)
        self._normalize_issue_and_suggestion_types(parsed)
        self._normalize_payload(parsed)
        return ProcessAnalysisResponse.model_validate(parsed)

    def _build_prompt(self, payload: ProcessAnalysisRequest) -> str:
        metrics_json = json.dumps(payload.metrics or {}, ensure_ascii=False)
        return (
            "Eres un analista senior de procesos BPMN para un sistema BPM colaborativo.\n"
            "Analiza el XML BPMN y las metricas reales si existen. Detecta riesgos de optimizacion, "
            "cuellos de botella, validaciones faltantes, gateways ambiguos, tareas redundantes y problemas de lanes.\n"
            "Devuelve SOLO JSON valido, sin markdown, sin explicaciones fuera del JSON.\n"
            "Si no hay problemas, usa issues: [] y suggestions: [].\n"
            "Los tipos permitidos para issues son exactamente: bottleneck, redundancy, missing_validation, inefficiency, gateway_problem, lane_problem.\n"
            "Si detectas un problema similar a un gateway ambiguo, usa gateway_problem. Si detectas un problema de lane, usa lane_problem.\n"
            "Usa elementId o relatedElementId solo cuando puedas identificar un id BPMN real del XML.\n"
            "No inventes ids de elementos.\n\n"
            "Formato obligatorio:\n"
            "{\n"
            '  "summary": "Resumen general del proceso",\n'
            '  "score": 0,\n'
            '  "issues": [\n'
            '    {"type": "bottleneck", "description": "Problema detectado", "elementId": "Activity_1", "severity": "high"}\n'
            "  ],\n"
            '  "suggestions": [\n'
            '    {"title": "Sugerencia", "description": "Explicacion clara", "impact": "Mejora esperada", "relatedElementId": "Activity_1", "canBeAppliedAutomatically": false}\n'
            "  ]\n"
            "}\n\n"
            f"Nombre del proceso: {payload.processName}\n"
            f"Metricas: {metrics_json}\n"
            f"XML BPMN:\n{payload.processXml}"
        )

    def _parse_json(self, raw_response: str) -> dict[str, Any]:
        cleaned = self._clean_response(raw_response)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.exception("Process analysis response is not valid JSON")
            raise ValueError("Gemini no devolvio JSON valido para el analisis") from exc

        if not isinstance(parsed, dict):
            raise ValueError("La respuesta del analisis debe ser un objeto JSON")

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

    def _normalize_payload(self, payload: dict[str, Any]) -> None:
        payload.setdefault("summary", "Analisis generado sin resumen detallado.")
        payload.setdefault("score", 75)
        payload.setdefault("issues", [])
        payload.setdefault("suggestions", [])
        payload["score"] = max(0, min(100, int(payload.get("score") or 0)))
        if not isinstance(payload["issues"], list):
            payload["issues"] = []
        if not isinstance(payload["suggestions"], list):
            payload["suggestions"] = []

    def _normalize_issue_and_suggestion_types(self, payload: dict[str, Any]) -> None:
        issues = payload.get("issues")
        if isinstance(issues, list):
            for issue in issues:
                if isinstance(issue, dict):
                    issue["type"] = self._normalize_issue_type(issue.get("type"))

        suggestions = payload.get("suggestions")
        if isinstance(suggestions, list):
            for suggestion in suggestions:
                if isinstance(suggestion, dict):
                    related_id = suggestion.get("relatedElementId")
                    if related_id is not None:
                        suggestion["relatedElementId"] = str(related_id).strip() or None

    def _normalize_issue_type(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        aliases = {
            "ambiguous_gateway": "gateway_problem",
            "gateway_issue": "gateway_problem",
            "gateway_problem": "gateway_problem",
            "lane_issue": "lane_problem",
            "lane_problem": "lane_problem",
            "missing_validation": "missing_validation",
            "validation_missing": "missing_validation",
            "redundancy": "redundancy",
            "inefficiency": "inefficiency",
            "bottleneck": "bottleneck",
        }
        return aliases.get(normalized, "inefficiency")
