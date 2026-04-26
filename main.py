from fastapi import FastAPI

from routers.analysis import router as analysis_router
from routers.assistant import router as assistant_router
from routers.diagram import router as diagram_router
from utils.logger import get_logger

app = FastAPI(
    title="System AI Service",
    version="1.0.0",
    description="Microservicio de IA para el sistema BPM.",
)

logger = get_logger(__name__)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(assistant_router, prefix="/ai", tags=["assistant"])
app.include_router(analysis_router, prefix="/ai", tags=["analysis"])
app.include_router(diagram_router, prefix="/ai", tags=["diagram"])
