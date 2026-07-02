from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import String, Text, DateTime, Enum, Boolean, JSON, Index, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from libs.communication_shared.models.base import Base, TenantMixin, TimestampMixin


class PostalMessageStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    HELD = "held"
    BOUNCED = "bounced"
    FAILED = "failed"


class PostalServer(Base, TenantMixin, TimestampMixin):
    """
    Per-tenant Postal mail-server credentials.

    Postal supports multiple organizations / mail servers on one install,
    so each tenant can send through its own server with its own API key
    and verified sending domain.
    """

    __tablename__ = "postal_servers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_postal_servers_tenant_name"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    postal_url: Mapped[str] = mapped_column(String(512), nullable=False)
    api_key: Mapped[str] = mapped_column(String(256), nullable=False)
    from_email: Mapped[str] = mapped_column(String(256), nullable=False)
    from_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Public key from Postal used to verify incoming webhook signatures
    webhook_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PostalMessage(Base, TenantMixin, TimestampMixin):
    """
    Delivery-tracking record for a message sent through Postal.

    Created when the Postal API accepts a message; the status then follows
    Postal webhook events (MessageSent, MessageDelayed, MessageDeliveryFailed,
    MessageBounced, MessageLinkClicked, MessageLoaded).
    """

    __tablename__ = "postal_messages"
    __table_args__ = (
        Index("ix_postal_messages_tenant_status", "tenant_id", "status"),
        UniqueConstraint("postal_message_id", name="uq_postal_messages_message_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email_log_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("email_logs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    postal_server_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("postal_servers.id", ondelete="SET NULL"), nullable=True
    )
    # message_id returned by POST /api/v1/send/message
    postal_message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # per-recipient token from the API response ("messages" map)
    postal_message_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(256), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(PostalMessageStatus), nullable=False, default=PostalMessageStatus.PENDING
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)


class PostalWebhookEvent(Base, TimestampMixin):
    """
    Raw webhook event received from Postal, stored before processing.

    tenant_id is nullable because the event arrives keyed only by Postal's
    message id — the tenant is resolved afterwards via postal_messages.
    """

    __tablename__ = "postal_webhook_events"
    __table_args__ = (
        Index("ix_postal_webhook_events_message_id", "postal_message_id"),
        Index("ix_postal_webhook_events_event", "event"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    postal_message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
