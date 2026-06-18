from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, Text, DateTime, Boolean, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from libs.communication_shared.models.base import Base, TenantMixin, TimestampMixin


class InAppNotificationType(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"


class InAppNotification(Base, TenantMixin, TimestampMixin):
    __tablename__ = "in_app_notifications"
    __table_args__ = (
        Index("ix_in_app_tenant_recipient_unread", "tenant_id", "recipient_id", "is_read"),
        Index("ix_in_app_notification_id", "notification_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    notification_id: Mapped[str] = mapped_column(String(36), nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(32), default=InAppNotificationType.INFO, nullable=False
    )
    action_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
