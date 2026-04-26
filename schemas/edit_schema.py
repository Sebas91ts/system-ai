from pydantic import BaseModel, Field


class EditDiagramRequest(BaseModel):
    instruction: str = Field(min_length=1)
    currentXml: str = Field(min_length=1)


class EditDiagramResponse(BaseModel):
    xml: str
    message: str = "Diagrama editado correctamente"
