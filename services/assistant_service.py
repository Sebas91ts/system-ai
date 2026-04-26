from services.assistant_context import build_assistant_context
from services.gemini_service import GeminiService


class AssistantService:
    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service or GeminiService()

    def answer(self, message: str) -> str:
        context = build_assistant_context()
        prompt = (
            f"{context}\n\n"
            "Instrucciones:\n"
            "- Responde en español.\n"
            "- Sé breve, claro y accionable.\n"
            "- Usa rutas, pantallas y acciones reales del sistema si están en el contexto.\n"
            "- No expliques teoría BPM salvo que el usuario la pida.\n"
            "- Si algo no existe todavía, dilo claramente.\n\n"
            f"Usuario: {message.strip()}\nRespuesta:"
        )
        return self._gemini_service.generate_text(prompt)
