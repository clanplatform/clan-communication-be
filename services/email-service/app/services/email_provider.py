from __future__ import annotations

import uuid
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.email_log import EmailLog, EmailStatus
from app.schemas.email import SendEmailRequest
from app.services.providers.smtp_provider import SMTPProvider
from app.services.providers.sendgrid_provider import SendGridProvider
from app.services.providers.ses_provider import SESProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailProviderService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._providers = self._build_provider_chain()

    def _build_provider_chain(self):
        providers = [SMTPProvider()]
        if settings.SENDGRID_ENABLED:
            providers.append(SendGridProvider())
        if settings.AWS_SES_ENABLED:
            providers.append(SESProvider())
        return providers

    async def send(self, request: SendEmailRequest) -> EmailLog:
        log = EmailLog(
            id=str(uuid.uuid4()),
            tenant_id=request.tenant_id,
            notification_id=request.notification_id,
            recipient_email=request.to_email,
            from_email=request.from_email or settings.SMTP_FROM_EMAIL,
            subject=request.subject,
            body_html=request.body_html,
            body_text=request.body_text,
            provider="unknown",
            status=EmailStatus.PENDING,
            headers=request.headers,
        )
        self._db.add(log)
        await self._db.flush()

        last_error: Exception | None = None
        for provider in self._providers:
            try:
                log.status = EmailStatus.SENDING
                log.provider = provider.name
                message_id = await provider.send(
                    to_email=request.to_email,
                    from_email=request.from_email or settings.SMTP_FROM_EMAIL,
                    from_name=request.from_name or settings.SMTP_FROM_NAME,
                    subject=request.subject,
                    body_html=request.body_html,
                    body_text=request.body_text,
                    reply_to=request.reply_to,
                )
                log.provider_message_id = message_id
                log.status = EmailStatus.SENT
                log.sent_at = datetime.now(timezone.utc)
                await self._db.commit()
                logger.info(
                    "Email sent via %s: %s -> %s",
                    provider.name,
                    log.from_email,
                    log.recipient_email,
                )
                return log
            except Exception as exc:
                last_error = exc
                logger.warning("Provider %s failed: %s", provider.name, exc)
                log.retry_count += 1

        log.status = EmailStatus.FAILED
        log.error_detail = str(last_error)
        await self._db.commit()
        logger.error("All email providers failed for notification %s", request.notification_id)
        return log
