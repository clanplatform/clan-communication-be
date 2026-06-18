from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.models.notification import NotificationChannel, NotificationStatus


class NotificationCreate(BaseModel):
    recipient_id: str = Field(..., min_length=1, max_length=128)
    channel: NotificationChannel
    template_id: str | None = None
    subject: str | None = None
    body: str | None = None
    variables: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    scheduled_at: datetime | None = None
    correlation_id: str | None = None

    model_config = {"use_enum_values": True}


class BulkNotificationCreate(BaseModel):
    notifications: list[NotificationCreate] = Field(..., min_length=1, max_length=500)


class NotificationRead(BaseModel):
    id: str
    tenant_id: str
    recipient_id: str
    channel: str
    status: str
    template_id: str | None
    subject: str | None
    body: str | None
    retry_count: int
    sent_at: datetime | None
    failed_reason: str | None
    scheduled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    correlation_id: str | None

    model_config = {"from_attributes": True}


class NotificationUpdate(BaseModel):
    status: NotificationStatus | None = None
    failed_reason: str | None = None
    sent_at: datetime | None = None
