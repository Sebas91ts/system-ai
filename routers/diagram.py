from fastapi import APIRouter, HTTPException

from schemas.diagram_schema import DiagramRequest, DiagramResponse
from services.diagram_service import DiagramService
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
service = DiagramService()


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
        raise HTTPException(status_code=500, detail="No se pudo generar el diagrama") from exc
