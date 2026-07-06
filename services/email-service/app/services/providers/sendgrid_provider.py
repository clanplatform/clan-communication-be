from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.services.providers.base import ProviderSendResult

settings = get_settings()

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


class SendGridProvider:
    name = "sendgrid"

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
        content = []
        if body_text:
            content.append({"type": "text/plain", "value": body_text})
        if body_html:
            content.append({"type": "text/html", "value": body_html})

        payload: dict = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_email, "name": from_name},
            "subject": subject,
            "content": content,
        }
        if reply_to:
            payload["reply_to"] = {"email": reply_to}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                SENDGRID_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            return ProviderSendResult(
                message_id=resp.headers.get("X-Message-Id", "unknown")
            )
