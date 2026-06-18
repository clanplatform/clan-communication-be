from __future__ import annotations

from sqlalchemy import String, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import Any

from libs.communication_shared.models.base import Base, TenantMixin, TimestampMixin


class NotificationPreference(Base, TenantMixin, TimestampMixin):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "recipient_id", name="uq_preference_tenant_recipient"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recipient_id: Mapped[str] = mapped_column(String(128), nullable=False)
    channels_enabled: Mapped[list[str]] = mapped_column(
        JSON, default=lambda: ["email", "sms", "push", "in_app"], nullable=False
    )
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5), nullable=True)
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    custom_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
