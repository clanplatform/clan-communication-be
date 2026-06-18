from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, Text, DateTime, Enum, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column

from libs.communication_shared.models.base import Base, TenantMixin, TimestampMixin


class SmsStatus(StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNDELIVERED = "undelivered"


class SmsLog(Base, TenantMixin, TimestampMixin):
    __tablename__ = "sms_logs"
    __table_args__ = (
        Index("ix_sms_logs_tenant_status", "tenant_id", "status"),
        Index("ix_sms_logs_notification_id", "notification_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    notification_id: Mapped[str] = mapped_column(String(36), nullable=False)
    to_number: Mapped[str] = mapped_column(String(20), nullable=False)
    from_number: Mapped[str] = mapped_column(String(20), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(Enum(SmsStatus), nullable=False, default=SmsStatus.PENDING)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    segments: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
