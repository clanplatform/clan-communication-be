from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

settings = get_settings()


class SESProvider:
    name = "ses"

    def _client(self):
        return boto3.client(
            "ses",
            region_name=settings.AWS_SES_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

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
        body: dict = {}
        if body_text:
            body["Text"] = {"Data": body_text, "Charset": "UTF-8"}
        if body_html:
            body["Html"] = {"Data": body_html, "Charset": "UTF-8"}

        kwargs: dict = {
            "Source": f"{from_name} <{from_email}>",
            "Destination": {"ToAddresses": [to_email]},
            "Message": {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": body,
            },
        }
        if reply_to:
            kwargs["ReplyToAddresses"] = [reply_to]

        # boto3 SES is sync; run in executor for async compatibility
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self._client().send_email(**kwargs)
        )
        return response["MessageId"]
