from pydantic import BaseModel, Field


class TaskItem(BaseModel):
    name: str = Field(min_length=1)
    duration_minutes: float = Field(ge=0)
    area: str = Field(min_length=1)


class AnalysisRequest(BaseModel):
    tasks: list[TaskItem]


class AnalysisResponse(BaseModel):
    average_time_minutes: float
    slowest_tasks: list[TaskItem]
    overloaded_areas: list[dict[str, float | str]]
