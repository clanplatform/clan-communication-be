from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field


class SendEmailRequest(BaseModel):
    notification_id: str
    tenant_id: str
    recipient_id: str
    to_email: EmailStr
    from_email: EmailStr | None = None
    from_name: str | None = None
    subject: str = Field(..., min_length=1, max_length=512)
    body_html: str | None = None
    body_text: str | None = None
    headers: dict[str, str] | None = None
    reply_to: EmailStr | None = None


class EmailLogRead(BaseModel):
    id: str
    tenant_id: str
    notification_id: str
    recipient_email: str
    from_email: str
    subject: str
    provider: str
    provider_message_id: str | None
    status: str
    retry_count: int
    sent_at: datetime | None
    error_detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
