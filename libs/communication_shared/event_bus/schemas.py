from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
import uuid

from pydantic import BaseModel, Field


class EventType(StrEnum):
    NOTIFICATION_REQUESTED = "notification.requested"
    EMAIL_REQUESTED = "email.requested"
    SMS_REQUESTED = "sms.requested"
    PUSH_REQUESTED = "push.requested"
    IN_APP_REQUESTED = "in_app.requested"
    WHATSAPP_REQUESTED = "whatsapp.requested"

    EMAIL_SENT = "email.sent"
    EMAIL_FAILED = "email.failed"
    SMS_SENT = "sms.sent"
    SMS_FAILED = "sms.failed"
    PUSH_SENT = "push.sent"
    PUSH_FAILED = "push.failed"
    WHATSAPP_SENT = "whatsapp.sent"
    WHATSAPP_FAILED = "whatsapp.failed"

    NOTIFICATION_DELIVERED = "notification.delivered"
    NOTIFICATION_READ = "notification.read"


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    tenant_id: str
    correlation_id: str | None = None
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    payload: dict[str, Any]
    version: int = 1
