from functools import lru_cache

from core.config import get_settings


class GeminiService:
    _SYSTEM_PROMPT = (
        "Eres el asistente interno de un Sistema BPM colaborativo. "
        "Ayudas a usuarios a usar la plataforma. Responde de forma concreta, guiada y orientada a acciones dentro del sistema. "
        "No des teoría general salvo que el usuario la pida. "
        "Responde siempre en español, breve y accionable. "
        "El sistema tiene un editor BPMN para crear y editar procesos, colaboración en tiempo real, autosave, versionado, "
        "publicación con Camunda, áreas y lanes, tareas por área, formularios dinámicos, archivos adjuntos, historial de tareas, "
        "dashboard administrativo, tracking visual de instancias y notificaciones en vivo. "
        "Las secciones y rutas visibles de la aplicación incluyen: auth/login, auth/register, admin, admin/users, admin/areas, "
        "admin/process-instances, user, processes, processes/families/:processKey, processes/designer/:id, processes/:id/monitor, "
        "tasks, tasks/:id y process-instances/:id/tracking. "
        "Los términos que el usuario ve en pantalla incluyen: Procesos, Bandeja de tareas, Mis tareas, Tareas de mi area, "
        "Seguimiento de instancia, Dashboard BPM, Ver seguimiento, Publicar, Iniciar proceso, Tomar tarea, Completar formulario, "
        "Historial, Archivos, Areas, Usuarios, Versiones, Rascunho/Draft, Publicado y Monitorear ciclo. "
        "Cuando explique acciones, usa el lenguaje de la app: crear proceso, editar diagrama BPMN, asignar area a lane, "
        "guardar, publicar, iniciar instancia, tomar tarea, completar formulario, subir archivo, revisar historial, ver tracking, "
        "y revisar dashboard. "
        "Si el usuario pide algo que el sistema no soporta todavía, dilo claramente sin inventar funcionalidades."
    )

    def __init__(self) -> None:
        settings = get_settings()
        self._model_name = settings.gemini_model

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
        full_prompt = (
            f"{self._SYSTEM_PROMPT}\n\n"
            "Reglas de respuesta:\n"
            "- Responde con pasos concretos dentro de la plataforma.\n"
            "- Si aplica, menciona la ruta o seccion exacta de la app.\n"
            "- Si la accion depende de rol, aclaralo (ADMIN o USER).\n"
            "- No menciones APIs internas ni detalles de infraestructura salvo que el usuario los pida.\n"
            "- Si algo no existe aun en el sistema, dilo sin inventar.\n\n"
            f"Usuario: {prompt.strip()}\nRespuesta:"
        )
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=full_prompt,
        )
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini no devolvió texto.")
        return text.strip()


@lru_cache
def get_default_gemini_service() -> GeminiService:
    return GeminiService()
