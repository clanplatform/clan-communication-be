from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class PreferenceCreate(BaseModel):
    recipient_id: str
    channels_enabled: list[str] = ["email", "sms", "push", "in_app"]
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str = "UTC"
    unsubscribed: bool = False
    custom_settings: dict[str, Any] | None = None


class PreferenceUpdate(BaseModel):
    channels_enabled: list[str] | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None
    unsubscribed: bool | None = None
    custom_settings: dict[str, Any] | None = None


class PreferenceRead(BaseModel):
    id: str
    tenant_id: str
    recipient_id: str
    channels_enabled: list[str]
    quiet_hours_start: str | None
    quiet_hours_end: str | None
    timezone: str
    unsubscribed: bool

    model_config = {"from_attributes": True}
