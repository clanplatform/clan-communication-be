from __future__ import annotations

import httpx

from app.core.config import get_settings

settings = get_settings()


class PostalProvider:
    """
    Self-hosted Postal mail server (https://postalserver.io).

    Uses the Postal HTTP API: POST {POSTAL_URL}/api/v1/send/message
    authenticated with an X-Server-API-Key header (created per mail
    server in the Postal web UI under Credentials → API).

    Note: Postal returns HTTP 200 even on failure — errors are reported
    in the JSON body as {"status": "error", ...}, so the body must be
    checked explicitly.
    """

    name = "postal"

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
        payload: dict = {
            "to": [to_email],
            "from": f"{from_name} <{from_email}>" if from_name else from_email,
            "subject": subject,
        }
        if body_html:
            payload["html_body"] = body_html
        if body_text:
            payload["plain_body"] = body_text
        if reply_to:
            payload["reply_to"] = reply_to

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.POSTAL_URL.rstrip('/')}/api/v1/send/message",
                json=payload,
                headers={
                    "X-Server-API-Key": settings.POSTAL_API_KEY,
                    "Content-Type": "application/json",
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") != "success":
            detail = data.get("data", {})
            raise RuntimeError(
                f"Postal send failed: {detail.get('code', 'unknown')} — "
                f"{detail.get('message', data)}"
            )

        return str(data.get("data", {}).get("message_id", "unknown"))
