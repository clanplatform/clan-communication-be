from __future__ import annotations

from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=128)
    channel: str
    language: str = "en"
    subject_template: str | None = None
    body_template: str
    variables: list[str] | None = None


class TemplateRead(BaseModel):
    id: str
    tenant_id: str
    slug: str
    channel: str
    language: str
    subject_template: str | None
    body_template: str
    variables: list[str] | None
    is_active: bool
    version: int

    model_config = {"from_attributes": True}
