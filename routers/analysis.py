from fastapi import APIRouter, HTTPException

from schemas.analysis_schema import AnalysisRequest, AnalysisResponse
from schemas.process_analysis_schema import ProcessAnalysisRequest, ProcessAnalysisResponse
from services.analysis_service import AnalysisService
from services.process_analysis_service import ProcessAnalysisService
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
service = AnalysisService()
process_analysis_service = ProcessAnalysisService()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(payload: AnalysisRequest) -> AnalysisResponse:
    logger.info("Request received at /ai/analyze")
    return service.analyze(payload)


@router.post("/analyze-process", response_model=ProcessAnalysisResponse)
async def analyze_process(payload: ProcessAnalysisRequest) -> ProcessAnalysisResponse:
    logger.info("Request received at /ai/analyze-process")
    try:
        return process_analysis_service.analyze_process(payload)
    except ValueError as exc:
        logger.exception("Process analysis returned invalid payload")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Process analysis endpoint failed")
        if _is_gemini_quota_error(exc):
            raise HTTPException(
                status_code=503,
                detail="IA temporalmente no disponible por cuota de Gemini. Intenta mas tarde.",
            ) from exc
        raise HTTPException(status_code=503, detail="No se pudo analizar el proceso con IA") from exc


def _is_gemini_quota_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "429" in message
        or "resource_exhausted" in message
        or "quota exceeded" in message
    )
