from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "email-service"


@pytest.mark.asyncio
async def test_send_email_success(client: AsyncClient) -> None:
    smtp_send = AsyncMock(return_value="mock-message-id-123")

    with patch(
        "app.services.providers.smtp_provider.SMTPProvider.send",
        smtp_send,
    ):
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
async def test_send_email_provider_fallback(client: AsyncClient) -> None:
    smtp_fail = AsyncMock(side_effect=Exception("SMTP down"))

    with patch(
        "app.services.providers.smtp_provider.SMTPProvider.send",
        smtp_fail,
    ):
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
async def test_get_email_logs(client: AsyncClient) -> None:
    smtp_send = AsyncMock(return_value="log-test-msg-id")

    with patch(
        "app.services.providers.smtp_provider.SMTPProvider.send",
        smtp_send,
    ):
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
