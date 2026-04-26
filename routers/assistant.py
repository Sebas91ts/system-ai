from fastapi import APIRouter, HTTPException

from core.dependencies import get_gemini_service
from schemas.assistant_schema import AssistantRequest, AssistantResponse
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/assistant", response_model=AssistantResponse)
async def assistant(payload: AssistantRequest) -> AssistantResponse:
    logger.info("Request received at /ai/assistant")
    try:
        service = get_gemini_service()
        response = service.generate_text(payload.message)
        logger.info("Assistant response generated successfully")
        return AssistantResponse(response=response)
    except Exception as exc:
        logger.exception("Assistant endpoint failed")
        raise HTTPException(status_code=500, detail="No se pudo procesar la solicitud de IA") from exc
