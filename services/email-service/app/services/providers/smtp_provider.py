from __future__ import annotations

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.core.config import get_settings

settings = get_settings()


class SMTPProvider:
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
    ) -> str:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((from_name, from_email))
        msg["To"] = to_email
        if reply_to:
            msg["Reply-To"] = reply_to

        if body_text:
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
        )
        return f"smtp:{to_email}:{subject[:20]}"
