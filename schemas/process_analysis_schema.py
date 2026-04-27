from typing import Any, Literal

from pydantic import BaseModel, Field


class ProcessAnalysisRequest(BaseModel):
    processXml: str = Field(min_length=1)
    processName: str = Field(default="Proceso sin nombre")
    metrics: dict[str, Any] = Field(default_factory=dict)


class ProcessAnalysisIssue(BaseModel):
    type: Literal[
        "bottleneck",
        "redundancy",
        "missing_validation",
        "inefficiency",
        "gateway_problem",
        "lane_problem",
    ]
    description: str
    elementId: str | None = None
    severity: Literal["low", "medium", "high"]


class ProcessAnalysisSuggestion(BaseModel):
    title: str
    description: str
    impact: str
    relatedElementId: str | None = None
    canBeAppliedAutomatically: bool = False


class ProcessAnalysisResponse(BaseModel):
    summary: str
    score: int = Field(ge=0, le=100)
    issues: list[ProcessAnalysisIssue] = Field(default_factory=list)
    suggestions: list[ProcessAnalysisSuggestion] = Field(default_factory=list)
