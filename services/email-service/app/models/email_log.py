from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import String, Text, DateTime, Enum, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from libs.communication_shared.models.base import Base, TenantMixin, TimestampMixin


class EmailStatus(StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    BOUNCED = "bounced"
    FAILED = "failed"


class EmailLog(Base, TenantMixin, TimestampMixin):
    __tablename__ = "email_logs"
    __table_args__ = (
        Index("ix_email_logs_tenant_status", "tenant_id", "status"),
        Index("ix_email_logs_notification_id", "notification_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    notification_id: Mapped[str] = mapped_column(String(36), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(256), nullable=False)
    from_email: Mapped[str] = mapped_column(String(256), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(EmailStatus), nullable=False, default=EmailStatus.PENDING
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
