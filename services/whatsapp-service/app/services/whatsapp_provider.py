from __future__ import annotations

import uuid
from datetime import datetime, timezone
import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.whatsapp_log import WhatsAppLog, WhatsAppStatus

logger = logging.getLogger(__name__)
settings = get_settings()

META_API_URL = "https://graph.facebook.com/v19.0/{phone_id}/messages"


class WebJSProvider:
    """Delegate to Node.js whatsapp-web.js worker."""
    name = "webjs"

    async def send(self, to: str, body: str, media_url: str | None = None) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload: dict = {"to": to, "message": body}
            if media_url:
                payload["mediaUrl"] = media_url
            resp = await client.post(
                f"{settings.WHATSAPP_WEBJS_URL}/send",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json().get("messageId", "webjs-ok")


class MetaWAProvider:
    """WhatsApp Business Cloud API (Meta)."""
    name = "meta"

    async def send(self, to: str, body: str, media_url: str | None = None) -> str:
        payload: dict = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                META_API_URL.format(phone_id=settings.META_WA_PHONE_ID),
                json=payload,
                headers={"Authorization": f"Bearer {settings.META_WA_TOKEN}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("messages", [{}])[0].get("id", "meta-ok")


class WhatsAppProviderService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._providers = self._build_chain()

    def _build_chain(self):
        providers = []
        if settings.META_WA_ENABLED:
            providers.append(MetaWAProvider())
        providers.append(WebJSProvider())
        return providers

    async def send(
        self,
        notification_id: str,
        tenant_id: str,
        to_number: str,
        body: str,
        media_url: str | None = None,
    ) -> WhatsAppLog:
        log = WhatsAppLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            notification_id=notification_id,
            to_number=to_number,
            body=body,
            media_url=media_url,
            provider="unknown",
            status=WhatsAppStatus.PENDING,
        )
        self._db.add(log)
        await self._db.flush()

        last_error: Exception | None = None
        for provider in self._providers:
            try:
                log.provider = provider.name
                msg_id = await provider.send(to_number, body, media_url)
                log.provider_message_id = msg_id
                log.status = WhatsAppStatus.SENT
                log.sent_at = datetime.now(timezone.utc)
                await self._db.commit()
                logger.info("WhatsApp sent via %s to %s", provider.name, to_number)
                return log
            except Exception as exc:
                last_error = exc
                log.retry_count += 1
                logger.warning("WA provider %s failed: %s", provider.name, exc)

        log.status = WhatsAppStatus.FAILED
        log.error_detail = str(last_error)
        await self._db.commit()
        return log
