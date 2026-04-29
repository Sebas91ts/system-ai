from google.genai import types

from schemas.form_fill_schema import FormFillRequest, FormFillResponse
from services.gemini_service import GeminiService
from utils.logger import get_logger

logger = get_logger(__name__)


class FormFillService:
    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service or GeminiService()
        self._generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=FormFillResponse.model_json_schema(),
            max_output_tokens=2048,
            temperature=0.2,
            top_p=0.8,
        )

    def suggest_values(self, payload: FormFillRequest) -> FormFillResponse:
        prompt = self._build_prompt(payload)
        raw_response = self._gemini_service.generate_text(prompt, config=self._generation_config)
        logger.info("Gemini form-fill response received: %s", raw_response[:220])
        return FormFillResponse.model_validate_json(raw_response)

    def _build_prompt(self, payload: FormFillRequest) -> str:
        fields_block = []
        for field in payload.fields:
            options = ", ".join(field.options) if field.options else "sin opciones"
            fields_block.append(
                "\n".join(
                    [
                        f"- name: {field.name}",
                        f"  label: {field.label}",
                        f"  type: {field.type}",
                        f"  required: {field.required}",
                        f"  placeholder: {field.placeholder or ''}",
                        f"  helpText: {field.helpText or ''}",
                        f"  options: {options}",
                    ]
                )
            )

        return (
            "Eres un asistente de captura de datos para formularios BPM.\n"
            "Debes leer una transcripcion dictada por un funcionario y sugerir valores para completar campos del formulario.\n"
            "Devuelve SOLO JSON valido con este formato:\n"
            "{\n"
            '  "summary": "breve resumen",\n'
            '  "suggestions": [\n'
            '    {"fieldName": "campo", "value": "valor", "rationale": "opcional"}\n'
            "  ]\n"
            "}\n\n"
            "Reglas:\n"
            "- Responde en español.\n"
            "- Solo sugiere campos presentes en la lista recibida.\n"
            "- No inventes nombres de campo.\n"
            "- Si no hay evidencia suficiente para un campo, omítelo.\n"
            "- Para checkbox usa true o false.\n"
            "- Para checklist usa una lista de strings compatibles con las opciones.\n"
            "- Para select usa un unico valor exacto de las opciones disponibles.\n"
            "- Para number usa numero.\n"
            "- Para date usa formato YYYY-MM-DD si puede inferirse con confianza.\n"
            "- Nunca sugieras valores para campos file.\n"
            "- Respeta valores ya existentes: si currentValues ya trae algo coherente, no lo contradigas sin motivo fuerte.\n"
            "- Si la transcripcion menciona datos libres, prioriza text y textarea.\n\n"
            f"Proceso: {payload.processName or 'Sin nombre'}\n"
            f"Tarea: {payload.taskName or 'Sin nombre'}\n"
            f"Area: {payload.areaName or 'Sin area'}\n"
            f"Transcripcion del funcionario:\n{payload.transcript.strip()}\n\n"
            f"Valores actuales:\n{payload.currentValues}\n\n"
            "Campos disponibles:\n"
            f"{'\n\n'.join(fields_block) if fields_block else '- Sin campos'}"
        )
