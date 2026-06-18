from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.sms_log import SmsLog, SmsStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class TwilioProvider:
    name = "twilio"

    async def send(self, to: str, from_: str, body: str) -> str:
        from twilio.rest import Client
        import asyncio
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        loop = asyncio.get_event_loop()
        msg = await loop.run_in_executor(
            None,
            lambda: client.messages.create(body=body, from_=from_, to=to)
        )
        return msg.sid


class VonageProvider:
    name = "vonage"

    async def send(self, to: str, from_: str, body: str) -> str:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://rest.nexmo.com/sms/json",
                data={
                    "api_key": settings.VONAGE_API_KEY,
                    "api_secret": settings.VONAGE_API_SECRET,
                    "from": from_ or settings.VONAGE_FROM,
                    "to": to,
                    "text": body,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            messages = data.get("messages", [])
            if not messages or messages[0].get("status") != "0":
                raise RuntimeError(f"Vonage error: {data}")
            return messages[0].get("message-id", "unknown")


class SmsProviderService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._providers = self._build_chain()

    def _build_chain(self):
        providers = []
        if settings.TWILIO_ENABLED:
            providers.append(TwilioProvider())
        if settings.VONAGE_ENABLED:
            providers.append(VonageProvider())
        return providers

    async def send(
        self,
        notification_id: str,
        tenant_id: str,
        to_number: str,
        body: str,
        from_number: str | None = None,
    ) -> SmsLog:
        from_num = from_number or settings.TWILIO_FROM_NUMBER
        segments = math.ceil(len(body) / settings.MAX_SMS_LENGTH)

        log = SmsLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            notification_id=notification_id,
            to_number=to_number,
            from_number=from_num,
            body=body,
            provider="unknown",
            status=SmsStatus.PENDING,
            segments=segments,
        )
        self._db.add(log)
        await self._db.flush()

        last_error: Exception | None = None
        for provider in self._providers:
            try:
                log.status = SmsStatus.SENDING
                log.provider = provider.name
                msg_id = await provider.send(to_number, from_num, body)
                log.provider_message_id = msg_id
                log.status = SmsStatus.SENT
                log.sent_at = datetime.now(timezone.utc)
                await self._db.commit()
                logger.info("SMS sent via %s to %s", provider.name, to_number)
                return log
            except Exception as exc:
                last_error = exc
                log.retry_count += 1
                logger.warning("SMS provider %s failed: %s", provider.name, exc)

        log.status = SmsStatus.FAILED
        log.error_detail = str(last_error)
        await self._db.commit()
        return log
