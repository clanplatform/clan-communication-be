from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.push_log import PushLog, PushStatus, DevicePlatform

logger = logging.getLogger(__name__)
settings = get_settings()

FCM_SEND_URL = "https://fcm.googleapis.com/fcm/send"


class FCMProvider:
    name = "fcm"

    async def send(
        self,
        device_token: str,
        title: str | None,
        body: str,
        data: dict[str, Any] | None,
    ) -> str:
        payload: dict = {
            "to": device_token,
            "notification": {"body": body},
        }
        if title:
            payload["notification"]["title"] = title
        if data:
            payload["data"] = data

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                FCM_SEND_URL,
                json=payload,
                headers={
                    "Authorization": f"key={settings.FCM_SERVER_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("failure", 1) > 0:
                error = result.get("results", [{}])[0].get("error", "unknown")
                raise RuntimeError(f"FCM delivery failure: {error}")
            return result.get("results", [{}])[0].get("message_id", "fcm-ok")


class PushProviderService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def send(
        self,
        notification_id: str,
        tenant_id: str,
        device_token: str,
        platform: str,
        body: str,
        title: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> PushLog:
        log = PushLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            notification_id=notification_id,
            device_token=device_token,
            platform=platform,
            title=title,
            body=body,
            data=data,
            provider="fcm",
            status=PushStatus.PENDING,
        )
        self._db.add(log)
        await self._db.flush()

        try:
            provider = FCMProvider()
            log.status = PushStatus.SENT
            msg_id = await provider.send(device_token, title, body, data)
            log.provider_message_id = msg_id
            log.sent_at = datetime.now(timezone.utc)
            await self._db.commit()
            logger.info("Push sent to %s via FCM", device_token[:10])
        except Exception as exc:
            log.status = PushStatus.FAILED
            log.error_detail = str(exc)
            log.retry_count += 1
            await self._db.commit()
            logger.error("Push failed for notification %s: %s", notification_id, exc)

        return log
