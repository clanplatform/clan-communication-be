"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("subject_template", sa.String(512), nullable=True),
        sa.Column("body_template", sa.Text, nullable=False),
        sa.Column("variables", sa.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "slug", "channel", name="uq_template_tenant_slug_channel"),
    )
    op.create_index("ix_templates_tenant", "notification_templates", ["tenant_id"])

    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("recipient_id", sa.String(128), nullable=False),
        sa.Column("channels_enabled", sa.JSON, nullable=False),
        sa.Column("quiet_hours_start", sa.String(5), nullable=True),
        sa.Column("quiet_hours_end", sa.String(5), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("unsubscribed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("custom_settings", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "recipient_id", name="uq_preference_tenant_recipient"),
    )
    op.create_index("ix_preferences_tenant", "notification_preferences", ["tenant_id"])

    channel_enum = sa.Enum(
        "email", "sms", "push", "in_app", "whatsapp", name="notificationchannel"
    )
    status_enum = sa.Enum(
        "pending", "queued", "sending", "delivered", "failed", "cancelled",
        name="notificationstatus"
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("recipient_id", sa.String(128), nullable=False),
        sa.Column("channel", channel_enum, nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("template_id", sa.String(64), nullable=True),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_reason", sa.Text, nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_tenant_status", "notifications", ["tenant_id", "status"])
    op.create_index("ix_notifications_tenant_recipient", "notifications", ["tenant_id", "recipient_id"])
    op.create_index("ix_notifications_correlation", "notifications", ["correlation_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("notification_preferences")
    op.drop_table("notification_templates")
    sa.Enum(name="notificationchannel").drop(op.get_bind())
    sa.Enum(name="notificationstatus").drop(op.get_bind())
