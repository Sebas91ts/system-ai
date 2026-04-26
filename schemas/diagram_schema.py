from pydantic import BaseModel, Field


class DiagramRequest(BaseModel):
    text: str = Field(min_length=1)


class DiagramTask(BaseModel):
    id: str
    name: str
    area: str | None = None


class DiagramFlow(BaseModel):
    from_task: str
    to_task: str


class DiagramArea(BaseModel):
    name: str


class DiagramResponse(BaseModel):
    tasks: list[DiagramTask]
    flows: list[DiagramFlow]
    areas: list[DiagramArea]
