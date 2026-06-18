from __future__ import annotations

from sqlalchemy import String, Text, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import Any

from libs.communication_shared.models.base import Base, TenantMixin, TimestampMixin


class NotificationTemplate(Base, TenantMixin, TimestampMixin):
    __tablename__ = "notification_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", "channel", name="uq_template_tenant_slug_channel"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    subject_template: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
