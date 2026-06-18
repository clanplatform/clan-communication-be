from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class SendSmsRequest(BaseModel):
    notification_id: str
    tenant_id: str
    recipient_id: str
    to_number: str = Field(..., pattern=r"^\+?[1-9]\d{7,14}$")
    body: str = Field(..., min_length=1, max_length=1600)
    from_number: str | None = None


class SmsLogRead(BaseModel):
    id: str
    tenant_id: str
    notification_id: str
    to_number: str
    from_number: str
    body: str
    provider: str
    provider_message_id: str | None
    status: str
    retry_count: int
    sent_at: datetime | None
    error_detail: str | None
    segments: int
    created_at: datetime

    model_config = {"from_attributes": True}
