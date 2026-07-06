from __future__ import annotations

import pytest
from unittest.mock import patch
from httpx import AsyncClient

from app.services.email_provider import EmailProviderService
from app.services.providers.base import ProviderSendResult


class FakeProvider:
    """Stand-in for a real provider (SMTP/SendGrid/SES) in the chain."""

    name = "fake"

    def __init__(self, message_id: str | None = None, error: Exception | None = None):
        self._message_id = message_id
        self._error = error

    async def send(self, **kwargs) -> ProviderSendResult:
        if self._error:
            raise self._error
        return ProviderSendResult(message_id=self._message_id or "fake-message-id")


def patch_provider_chain(*providers: FakeProvider):
    return patch.object(
        EmailProviderService,
        "_build_provider_chain",
        return_value=list(providers),
    )


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "email-service"


@pytest.mark.asyncio
async def test_send_email_success(client: AsyncClient) -> None:
    with patch_provider_chain(FakeProvider(message_id="mock-message-id-123")):
        resp = await client.post(
            "/api/v1/send",
            json={
                "notification_id": "notif-001",
                "tenant_id": "tenant-abc",
                "recipient_id": "user-001",
                "to_email": "user@example.com",
                "subject": "Test Email",
                "body_html": "<p>Hello World</p>",
                "body_text": "Hello World",
            },
        )

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "sent"
    assert data["notification_id"] == "notif-001"
    assert data["tenant_id"] == "tenant-abc"


@pytest.mark.asyncio
async def test_send_email_all_providers_fail(client: AsyncClient) -> None:
    with patch_provider_chain(FakeProvider(error=Exception("provider down"))):
        resp = await client.post(
            "/api/v1/send",
            json={
                "notification_id": "notif-002",
                "tenant_id": "tenant-abc",
                "recipient_id": "user-002",
                "to_email": "fallback@example.com",
                "subject": "Fallback Test",
                "body_text": "Fallback body",
            },
        )

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "failed"


@pytest.mark.asyncio
async def test_send_email_no_provider_configured(client: AsyncClient) -> None:
    with patch_provider_chain():
        resp = await client.post(
            "/api/v1/send",
            json={
                "notification_id": "notif-noprov",
                "tenant_id": "tenant-abc",
                "recipient_id": "user-noprov",
                "to_email": "noprov@example.com",
                "subject": "No Provider Test",
                "body_text": "No provider body",
            },
        )

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "failed"
    assert "no email provider configured" in data["error_detail"]


@pytest.mark.asyncio
async def test_get_email_logs(client: AsyncClient) -> None:
    with patch_provider_chain(FakeProvider(message_id="log-test-msg-id")):
        send_resp = await client.post(
            "/api/v1/send",
            json={
                "notification_id": "notif-log-003",
                "tenant_id": "tenant-abc",
                "recipient_id": "user-003",
                "to_email": "log@example.com",
                "subject": "Log Test",
                "body_text": "Log body",
            },
        )
    assert send_resp.status_code == 202

    logs_resp = await client.get("/api/v1/send/logs/notif-log-003")
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) >= 1
    assert logs[0]["notification_id"] == "notif-log-003"


@pytest.mark.asyncio
async def test_send_email_invalid_payload(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/send",
        json={
            "notification_id": "notif-bad",
            "tenant_id": "tenant-abc",
            "recipient_id": "user-bad",
            "to_email": "not-an-email",
            "subject": "Bad",
        },
    )
    assert resp.status_code == 422
