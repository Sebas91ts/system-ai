from pydantic import BaseModel, Field


class DiagramRequest(BaseModel):
    text: str = Field(min_length=1)


class DiagramTask(BaseModel):
    id: str
    name: str
    area: str | None = None
    type: str = "userTask"


class DiagramFlow(BaseModel):
    from_: str = Field(alias="from")
    to: str
    condition: str | None = None

    model_config = {"populate_by_name": True}


class DiagramGateway(BaseModel):
    id: str
    type: str = Field(pattern="^(exclusive|parallel|inclusive)$")
    condition: str | None = None


class DiagramArea(BaseModel):
    name: str


class DiagramResponse(BaseModel):
    processName: str
    tasks: list[DiagramTask]
    gateways: list[DiagramGateway] = Field(default_factory=list)
    flows: list[DiagramFlow]
    areas: list[str] = Field(default_factory=list)
