from fastapi import APIRouter, HTTPException

from schemas.diagram_schema import DiagramRequest, DiagramResponse
from schemas.edit_schema import EditDiagramRequest, EditDiagramResponse
from services.diagram_service import DiagramService
from services.edit_service import EditService
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
service = DiagramService()
edit_service = EditService()


@router.post("/generate-diagram", response_model=DiagramResponse)
async def generate_diagram(payload: DiagramRequest) -> DiagramResponse:
    logger.info("Request received at /ai/generate-diagram")
    try:
        return service.generate_structure(payload.text)
    except ValueError as exc:
        logger.warning("Invalid diagram payload: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Generate diagram endpoint failed")
        if _is_gemini_quota_error(exc):
            raise HTTPException(
                status_code=503,
                detail="IA temporalmente no disponible por cuota de Gemini. Intenta mas tarde.",
            ) from exc
        raise HTTPException(status_code=500, detail="No se pudo generar el diagrama") from exc


@router.post("/edit-diagram", response_model=EditDiagramResponse)
async def edit_diagram(payload: EditDiagramRequest) -> EditDiagramResponse:
    logger.info("Request received at /ai/edit-diagram")
    try:
        return edit_service.edit_xml(payload)
    except RuntimeError as exc:
        logger.warning("Gemini unavailable while editing diagram: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        logger.warning("Invalid edit diagram payload: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Edit diagram endpoint failed")
        if _is_gemini_quota_error(exc):
            raise HTTPException(
                status_code=503,
                detail="IA temporalmente no disponible por cuota de Gemini. Intenta mas tarde.",
            ) from exc
        raise HTTPException(status_code=500, detail="No se pudo editar el diagrama") from exc


def _is_gemini_quota_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "429" in message
        or "resource_exhausted" in message
        or "quota exceeded" in message
    )
