from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.models.notification import Notification, NotificationStatus, NotificationChannel
from app.models.preference import NotificationPreference
from app.schemas.notification import NotificationCreate, NotificationUpdate
from app.services.template_service import TemplateService
from app.services.dispatcher import ChannelDispatcher
from libs.communication_shared.exceptions import RateLimitError
import redis.asyncio as aioredis

import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        db: AsyncSession,
        redis: aioredis.Redis,
        dispatcher: ChannelDispatcher,
        template_service: TemplateService,
    ) -> None:
        self._db = db
        self._redis = redis
        self._dispatcher = dispatcher
        self._template_service = template_service

    async def _check_rate_limit(self, tenant_id: str) -> None:
        key = f"rate:{tenant_id}:minute"
        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, 60)
        if count > 1000:
            raise RateLimitError(tenant_id, 1000)

    async def _check_preference(
        self, tenant_id: str, recipient_id: str, channel: str
    ) -> bool:
        result = await self._db.execute(
            select(NotificationPreference).where(
                NotificationPreference.tenant_id == tenant_id,
                NotificationPreference.recipient_id == recipient_id,
            )
        )
        pref = result.scalar_one_or_none()
        if pref is None:
            return True
        if pref.unsubscribed:
            return False
        return channel in pref.channels_enabled

    async def create(
        self, tenant_id: str, data: NotificationCreate
    ) -> Notification:
        await self._check_rate_limit(tenant_id)

        allowed = await self._check_preference(
            tenant_id, data.recipient_id, data.channel
        )
        if not allowed:
            raise ValueError(
                f"Recipient {data.recipient_id} has opted out of {data.channel}"
            )

        subject = data.subject
        body = data.body

        if data.template_id and data.variables:
            rendered = await self._template_service.render(
                tenant_id, data.template_id, data.channel, data.variables
            )
            subject = rendered.get("subject", subject)
            body = rendered.get("body", body)

        notification = Notification(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            recipient_id=data.recipient_id,
            channel=data.channel,
            status=NotificationStatus.PENDING,
            template_id=data.template_id,
            subject=subject,
            body=body,
            metadata_=data.metadata,
            scheduled_at=data.scheduled_at,
            correlation_id=data.correlation_id,
        )
        self._db.add(notification)
        await self._db.flush()

        if not data.scheduled_at:
            await self._dispatcher.dispatch(notification)
            notification.status = NotificationStatus.QUEUED

        await self._db.commit()
        await self._db.refresh(notification)
        return notification

    async def bulk_create(
        self, tenant_id: str, notifications: list[NotificationCreate]
    ) -> list[Notification]:
        results = []
        for item in notifications:
            notif = await self.create(tenant_id, item)
            results.append(notif)
        return results

    async def get(self, tenant_id: str, notification_id: str) -> Notification | None:
        result = await self._db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_recipient(
        self,
        tenant_id: str,
        recipient_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int]:
        offset = (page - 1) * page_size
        q = (
            select(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.recipient_id == recipient_id,
            )
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        count_q = select(func.count()).where(
            Notification.tenant_id == tenant_id,
            Notification.recipient_id == recipient_id,
        )
        rows = (await self._db.execute(q)).scalars().all()
        total = (await self._db.execute(count_q)).scalar_one()
        return list(rows), total

    async def update_status(
        self,
        tenant_id: str,
        notification_id: str,
        update_data: NotificationUpdate,
    ) -> Notification | None:
        notif = await self.get(tenant_id, notification_id)
        if notif is None:
            return None
        for field, value in update_data.model_dump(exclude_none=True).items():
            setattr(notif, field, value)
        await self._db.commit()
        await self._db.refresh(notif)
        return notif
