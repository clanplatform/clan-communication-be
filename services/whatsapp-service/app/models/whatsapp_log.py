from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, Text, DateTime, Enum, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from libs.communication_shared.models.base import Base, TenantMixin, TimestampMixin


class WhatsAppStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class WhatsAppLog(Base, TenantMixin, TimestampMixin):
    __tablename__ = "whatsapp_logs"
    __table_args__ = (
        Index("ix_wa_logs_tenant_status", "tenant_id", "status"),
        Index("ix_wa_logs_notification_id", "notification_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    notification_id: Mapped[str] = mapped_column(String(36), nullable=False)
    to_number: Mapped[str] = mapped_column(String(20), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(WhatsAppStatus), nullable=False, default=WhatsAppStatus.PENDING
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
