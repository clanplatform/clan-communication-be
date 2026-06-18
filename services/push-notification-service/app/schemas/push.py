from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel

from app.models.push_log import DevicePlatform


class SendPushRequest(BaseModel):
    notification_id: str
    tenant_id: str
    recipient_id: str
    device_token: str
    platform: DevicePlatform
    title: str | None = None
    body: str
    data: dict[str, Any] | None = None

    model_config = {"use_enum_values": True}


class PushLogRead(BaseModel):
    id: str
    tenant_id: str
    notification_id: str
    device_token: str
    platform: str
    title: str | None
    body: str
    provider: str
    provider_message_id: str | None
    status: str
    retry_count: int
    sent_at: datetime | None
    error_detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
