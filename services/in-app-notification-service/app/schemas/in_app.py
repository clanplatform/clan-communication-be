from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel

from app.models.in_app_notification import InAppNotificationType


class SendInAppRequest(BaseModel):
    notification_id: str
    tenant_id: str
    recipient_id: str
    title: str | None = None
    body: str
    notification_type: InAppNotificationType = InAppNotificationType.INFO
    action_url: str | None = None
    expires_at: datetime | None = None
    extra_data: dict[str, Any] | None = None

    model_config = {"use_enum_values": True}


class InAppNotificationRead(BaseModel):
    id: str
    tenant_id: str
    notification_id: str
    recipient_id: str
    title: str | None
    body: str
    notification_type: str
    action_url: str | None
    is_read: bool
    read_at: datetime | None
    expires_at: datetime | None
    extra_data: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
