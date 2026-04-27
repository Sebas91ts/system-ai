import json
from typing import Any

from google.genai import types

from schemas.process_analysis_schema import ProcessAnalysisRequest, ProcessAnalysisResponse
from services.gemini_service import GeminiService
from utils.logger import get_logger

logger = get_logger(__name__)


class ProcessAnalysisService:
    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service or GeminiService()
        self._generation_config = self._build_generation_config()

    def analyze_process(self, payload: ProcessAnalysisRequest) -> ProcessAnalysisResponse:
        prompt = self._build_prompt(payload)
        raw_response = self._gemini_service.generate_text(prompt, config=self._generation_config)
        logger.info("Gemini process analysis response received: %s", raw_response[:220])
        parsed = self._parse_json(raw_response)
        self._normalize_issue_and_suggestion_types(parsed)
        self._normalize_payload(parsed)
        return ProcessAnalysisResponse.model_validate(parsed)

    def _build_generation_config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=ProcessAnalysisResponse.model_json_schema(),
            max_output_tokens=12000,
            temperature=0.15,
            top_p=0.8,
        )

    def _build_prompt(self, payload: ProcessAnalysisRequest) -> str:
        metrics_json = json.dumps(payload.metrics or {}, ensure_ascii=False)
        return (
            "Eres un analista senior de procesos BPMN para un sistema BPM colaborativo.\n"
            "Analiza el XML BPMN y las metricas reales si existen. Detecta riesgos de optimizacion, "
            "cuellos de botella, validaciones faltantes, gateways ambiguos, tareas redundantes y problemas de lanes.\n"
            "Devuelve SOLO JSON valido y estricto, sin markdown, sin explicaciones fuera del JSON.\n"
            "Si no hay problemas, usa issues: [] y suggestions: [].\n"
            "Los tipos permitidos para issues son exactamente: bottleneck, redundancy, missing_validation, inefficiency, gateway_problem, lane_problem.\n"
            "Si detectas un problema similar a un gateway ambiguo, usa gateway_problem. Si detectas un problema de lane, usa lane_problem.\n"
            "Usa elementId o relatedElementId solo cuando puedas identificar un id BPMN real del XML.\n"
            "No inventes ids de elementos.\n"
            "Para suggestions, canBeAppliedAutomatically debe ser un booleano JSON real true o false.\n"
            "Solo incluye proposedXml cuando la correccion sea simple, segura y local.\n"
            "Si la mejora requiere redisenar el proceso, cambiar areas, eliminar pasos importantes o una decision humana compleja, usa canBeAppliedAutomatically=false y proposedXml=null.\n"
            "Cuando incluyas proposedXml, devuelve el XML BPMN completo y valido, no fragmentos, conservando IDs existentes, processKey, collaboration, participant, lanes, custom:areaRef y BPMNDI.\n"
            "Si el XML propuesto es largo, prioriza solo las sugerencias realmente automáticas y evita duplicar XML innecesariamente.\n\n"
            "Formato obligatorio:\n"
            "{\n"
            '  "summary": "Resumen general del proceso",\n'
            '  "score": 0,\n'
            '  "issues": [\n'
            '    {"type": "bottleneck", "description": "Problema detectado", "elementId": "Activity_1", "severity": "high"}\n'
            "  ],\n"
            '  "suggestions": [\n'
            '    {"title": "Sugerencia", "description": "Explicacion clara", "impact": "Mejora esperada", "relatedElementId": "Activity_1", "canBeAppliedAutomatically": false, "proposedXml": null}\n'
            "  ]\n"
            "}\n\n"
            "Reglas para suggestions:\n"
            "- Solo incluye proposedXml cuando el cambio sea simple, seguro y aplicable automaticamente.\n"
            "- Si detectas una mejora simple y concreta, canBeAppliedAutomatically debe ser true y proposedXml debe venir completo.\n"
            "- Ejemplos adecuados: agregar una condicion faltante en un gateway, corregir una condicion mal formada, agregar un endEvent faltante, renombrar una tarea o agregar un flujo de salida obvio.\n"
            "- Si el cambio requiere redisenar el proceso, cambiar areas, eliminar pasos importantes o tomar una decision humana compleja, usa canBeAppliedAutomatically=false y proposedXml=null.\n"
            "- Cuando incluyas proposedXml, devuelve el XML BPMN completo y valido, no fragmentos, conservando IDs existentes, processKey, collaboration, participant, lanes, custom:areaRef y BPMNDI.\n"
            "- proposedXml debe ser texto plano del XML completo, sin markdown, sin bloques de codigo y sin explicaciones adicionales.\n\n"
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

                    suggestion["canBeAppliedAutomatically"] = self._parse_bool(
                        suggestion.get("canBeAppliedAutomatically")
                    )

                    proposed_xml = suggestion.get("proposedXml")
                    if not suggestion["canBeAppliedAutomatically"]:
                        suggestion["proposedXml"] = None
                    elif isinstance(proposed_xml, str):
                        cleaned_xml = proposed_xml.strip()
                        if cleaned_xml.startswith("```"):
                            cleaned_xml = cleaned_xml.removeprefix("```xml").removeprefix("```").strip()
                            if cleaned_xml.endswith("```"):
                                cleaned_xml = cleaned_xml[:-3].strip()
                        suggestion["proposedXml"] = cleaned_xml or None
                    else:
                        suggestion["proposedXml"] = None

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

    def _parse_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False

        normalized = str(value).strip().lower()
        return normalized in {"true", "1", "yes", "y", "si", "sí"}
