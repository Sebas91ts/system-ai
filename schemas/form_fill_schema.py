from typing import Any, Literal

from pydantic import BaseModel, Field


FormFillFieldType = Literal["text", "textarea", "number", "date", "select", "checkbox", "checklist", "file"]


class FormFillFieldContext(BaseModel):
    name: str = Field(min_length=1)
    label: str = Field(min_length=1)
    type: FormFillFieldType
    required: bool = False
    placeholder: str | None = None
    helpText: str | None = None
    options: list[str] = Field(default_factory=list)


class FormFillRequest(BaseModel):
    transcript: str = Field(min_length=1)
    processName: str | None = None
    taskName: str | None = None
    areaName: str | None = None
    currentValues: dict[str, Any] = Field(default_factory=dict)
    fields: list[FormFillFieldContext] = Field(default_factory=list)


class FormFillSuggestion(BaseModel):
    fieldName: str
    value: str | float | bool | list[str] | None = None
    rationale: str | None = None


class FormFillResponse(BaseModel):
    summary: str
    suggestions: list[FormFillSuggestion] = Field(default_factory=list)
