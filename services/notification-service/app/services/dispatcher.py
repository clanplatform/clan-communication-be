from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from app.core.config import get_settings
from app.models.notification import Notification, NotificationChannel

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)
settings = get_settings()

CHANNEL_URLS: dict[str, str] = {
    NotificationChannel.EMAIL: settings.EMAIL_SERVICE_URL,
    NotificationChannel.SMS: settings.SMS_SERVICE_URL,
    NotificationChannel.PUSH: settings.PUSH_SERVICE_URL,
    NotificationChannel.IN_APP: settings.IN_APP_SERVICE_URL,
    NotificationChannel.WHATSAPP: settings.WHATSAPP_SERVICE_URL,
}


class ChannelDispatcher:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._client = http_client

    async def dispatch(self, notification: Notification) -> None:
        base_url = CHANNEL_URLS.get(notification.channel)
        if not base_url:
            logger.error("No service URL for channel %s", notification.channel)
            return

        payload = {
            "notification_id": notification.id,
            "tenant_id": notification.tenant_id,
            "recipient_id": notification.recipient_id,
            "subject": notification.subject,
            "body": notification.body,
            "metadata": notification.metadata_,
        }

        try:
            resp = await self._client.post(
                f"{base_url}/api/v1/send",
                json=payload,
                timeout=10.0,
            )
            resp.raise_for_status()
            logger.info(
                "Dispatched notification %s to %s channel",
                notification.id,
                notification.channel,
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Dispatch failed for %s: HTTP %s", notification.id, exc.response.status_code
            )
            raise
        except httpx.RequestError as exc:
            logger.error("Dispatch network error for %s: %s", notification.id, exc)
            raise
