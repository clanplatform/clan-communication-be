from __future__ import annotations

import asyncio
import logging
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

import aiosmtplib

from app.core.config import get_settings
from app.services.providers.base import ProviderSendResult

settings = get_settings()
logger = logging.getLogger(__name__)


class SMTPProvider:
    """
    Standard SMTP relay (Gmail, Outlook, Mailgun, corporate servers, ...).

    Connects to SMTP_HOST:SMTP_PORT and authenticates with
    SMTP_USERNAME / SMTP_PASSWORD when provided. SMTP_USE_TLS enables
    STARTTLS (typically port 587); SMTP_USE_SSL opens an implicit TLS
    connection instead (typically port 465). Enable at most one.

    For Gmail: host smtp.gmail.com, port 587, SMTP_USE_TLS=true, and an
    App Password (Google Account → Security → 2-Step Verification →
    App passwords) as SMTP_PASSWORD.
    """

    name = "smtp"

    async def send(
        self,
        to_email: str,
        from_email: str,
        from_name: str,
        subject: str,
        body_html: str | None,
        body_text: str | None,
        reply_to: str | None = None,
    ) -> ProviderSendResult:
        message = EmailMessage()
        message["From"] = formataddr((from_name, from_email)) if from_name else from_email
        message["To"] = to_email
        message["Subject"] = subject
        message_id = make_msgid()
        message["Message-ID"] = message_id
        if reply_to:
            message["Reply-To"] = reply_to

        if body_text and body_html:
            message.set_content(body_text)
            message.add_alternative(body_html, subtype="html")
        elif body_html:
            message.set_content(body_html, subtype="html")
        else:
            message.set_content(body_text or "")

        use_ssl = settings.SMTP_USE_SSL
        # aiosmtplib rejects use_tls + start_tls together; SSL wins when both are set
        start_tls = False if use_ssl else settings.SMTP_USE_TLS

        # A cloud-hosted sender authenticating as a personal Gmail account can
        # occasionally hang rather than fail fast (Google's abuse detection
        # silently stalling the connection instead of rejecting outright) - one
        # extra attempt recovers transient cases; a persistent block will still
        # fail both times, which is fine, since EmailProviderService then falls
        # through to the next configured provider.
        last_error: Exception | None = None
        for attempt in range(1, 3):
            try:
                await aiosmtplib.send(
                    message,
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    username=settings.SMTP_USERNAME or None,
                    password=settings.SMTP_PASSWORD or None,
                    use_tls=use_ssl,
                    start_tls=start_tls,
                    timeout=20.0,
                )
                return ProviderSendResult(message_id=message_id.strip("<>"))
            except Exception as exc:
                last_error = exc
                logger.warning("SMTP attempt %d/2 failed for %s: %s", attempt, to_email, exc)
                if attempt < 2:
                    await asyncio.sleep(2.0)
        raise last_error
