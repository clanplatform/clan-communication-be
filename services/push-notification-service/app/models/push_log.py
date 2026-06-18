from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, Text, DateTime, Enum, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from libs.communication_shared.models.base import Base, TenantMixin, TimestampMixin


class PushStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class DevicePlatform(StrEnum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class PushLog(Base, TenantMixin, TimestampMixin):
    __tablename__ = "push_logs"
    __table_args__ = (
        Index("ix_push_logs_tenant_status", "tenant_id", "status"),
        Index("ix_push_logs_notification_id", "notification_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    notification_id: Mapped[str] = mapped_column(String(36), nullable=False)
    device_token: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(Enum(DevicePlatform), nullable=False)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(Enum(PushStatus), nullable=False, default=PushStatus.PENDING)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
