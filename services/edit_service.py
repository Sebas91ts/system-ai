import re
import xml.etree.ElementTree as ET

from schemas.edit_schema import EditDiagramRequest, EditDiagramResponse
from services.gemini_service import GeminiService
from utils.logger import get_logger

logger = get_logger(__name__)


class EditService:
    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service or GeminiService()

    def edit_xml(self, payload: EditDiagramRequest) -> EditDiagramResponse:
        prompt = (
            "Eres un asistente experto en BPMN.\n"
            "Recibiras un XML BPMN actual y una instruccion para modificarlo.\n"
            "Si la instruccion pide crear un proceso desde cero, usa el XML actual como base y devuelve un BPMN completo y coherente.\n"
            "Devuelve una nueva version completa del XML BPMN aplicando la instruccion.\n"
            "Conserva:\n"
            "- process id\n"
            "- process name\n"
            "- collaboration y participant si existen\n"
            "- lanes existentes\n"
            "- areas\n"
            "- formularios no deben modificarse\n"
            "- isExecutable=true\n"
            "- conexiones validas\n"
            "- BPMNDI valido\n"
            "- ids estables: no mezcles ids de tareas, gateways, flows ni lanes\n"
            "- si agregas elementos nuevos, crea ids nuevos pero coherentes y no reutilices ids existentes\n"
            "- respeta la estructura BPMN real del XML de entrada y no lo simplifiques a texto plano\n"
            "Devuelve SOLO XML BPMN valido, sin markdown, sin bloque de codigo y sin explicacion.\n\n"
            f"Instruccion: {payload.instruction.strip()}\n\n"
            f"XML actual:\n{payload.currentXml.strip()}"
        )

        try:
            raw_response, attempt = self._gemini_service.generate_text_with_attempts(prompt)
        except Exception as exc:
            if self._is_gemini_unavailable(exc):
                raise RuntimeError("Gemini está ocupado en este momento. Intenta nuevamente en unos segundos.") from exc
            raise
        logger.info("Gemini edit attempt %s completed", attempt)
        xml = self._extract_valid_xml(raw_response)
        if xml:
            return EditDiagramResponse(xml=xml)

        logger.warning("Primera respuesta de Gemini invalida; reintentando una vez con mas contexto.")
        retry_prompt = prompt + (
            "\n\nTu respuesta anterior no fue valida. Corrige estrictamente el XML BPMN.\n"
            "Recuerda: devuelve un XML BPMN bien formado, con tags cerrados correctamente, sin markdown y sin texto adicional."
        )
        retry_response, retry_attempt = self._gemini_service.generate_text_with_attempts(retry_prompt)
        logger.info("Gemini edit retry attempt %s completed", retry_attempt)
        xml = self._extract_valid_xml(retry_response)
        if xml:
            return EditDiagramResponse(xml=xml)

        raise ValueError("Gemini no devolvio XML BPMN valido para la edicion")

    def _clean_xml(self, raw_response: str) -> str:
        cleaned = self._strip_code_fences(raw_response.strip())

        match = re.search(r"(<\?xml[\s\S]*?</bpmn:definitions>)", cleaned)
        if match:
            return match.group(1).strip()

        start = cleaned.find("<bpmn:definitions")
        end = cleaned.rfind("</bpmn:definitions>")
        if start != -1 and end != -1 and end > start:
            return cleaned[start : end + len("</bpmn:definitions>")].strip()

        return cleaned

    def _strip_code_fences(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.startswith("```"):
            return cleaned

        cleaned = cleaned.removeprefix("```xml").removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        return cleaned

    def _validate_xml(self, xml: str) -> None:
        try:
            ET.fromstring(xml)
        except ET.ParseError as exc:
            logger.exception("Generated edit XML is not well formed")
            raise ValueError("Gemini devolvio XML BPMN mal formado para la edicion") from exc

    def _is_gemini_unavailable(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "503" in message or "unavailable" in message or "high demand" in message

    def _extract_valid_xml(self, raw_response: str) -> str | None:
        logger.info("Gemini edit response received: %s", raw_response[:200])
        xml = self._clean_xml(raw_response)
        if not xml.startswith("<?xml") and "<bpmn:definitions" not in xml:
            return None

        try:
            self._validate_xml(xml)
            return xml
        except ValueError:
            return None
