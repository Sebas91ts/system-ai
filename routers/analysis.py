from fastapi import APIRouter

from schemas.analysis_schema import AnalysisRequest, AnalysisResponse
from services.analysis_service import AnalysisService
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
service = AnalysisService()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(payload: AnalysisRequest) -> AnalysisResponse:
    logger.info("Request received at /ai/analyze")
    return service.analyze(payload)
