from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.core.config import get_settings
from app.core.database import get_db
from app.models.in_app_notification import InAppNotification
from app.schemas.in_app import SendInAppRequest, InAppNotificationRead
from libs.communication_shared.schemas.base import HealthResponse, PaginatedResponse

settings = get_settings()

router = APIRouter(prefix="/api/v1", tags=["in-app"])


@router.post("/send", response_model=InAppNotificationRead, status_code=status.HTTP_202_ACCEPTED)
async def send_in_app(request: SendInAppRequest, db: AsyncSession = Depends(get_db)) -> InAppNotificationRead:
    notif = InAppNotification(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        notification_id=request.notification_id,
        recipient_id=request.recipient_id,
        title=request.title,
        body=request.body,
        notification_type=request.notification_type,
        action_url=request.action_url,
        expires_at=request.expires_at,
        extra_data=request.extra_data,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    # Fire-and-forget WebSocket broadcast
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(
                f"{settings.WEBSOCKET_SERVICE_URL}/broadcast",
                json={
                    "tenant_id": request.tenant_id,
                    "recipient_id": request.recipient_id,
                    "event": "notification",
                    "data": InAppNotificationRead.model_validate(notif).model_dump(mode="json"),
                },
            )
    except Exception:
        pass

    return InAppNotificationRead.model_validate(notif)


@router.get("/notifications/{recipient_id}", response_model=PaginatedResponse[InAppNotificationRead])
async def list_notifications(
    recipient_id: str,
    tenant_id: str,
    unread_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[InAppNotificationRead]:
    q = select(InAppNotification).where(
        InAppNotification.tenant_id == tenant_id,
        InAppNotification.recipient_id == recipient_id,
    )
    if unread_only:
        q = q.where(InAppNotification.is_read.is_(False))
    q = q.order_by(InAppNotification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    count_q = select(func.count()).where(
        InAppNotification.tenant_id == tenant_id,
        InAppNotification.recipient_id == recipient_id,
    )
    if unread_only:
        count_q = count_q.where(InAppNotification.is_read.is_(False))

    rows = (await db.execute(q)).scalars().all()
    total = (await db.execute(count_q)).scalar_one()
    return PaginatedResponse(
        items=[InAppNotificationRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.patch("/notifications/{notification_id}/read", response_model=InAppNotificationRead)
async def mark_read(
    notification_id: str,
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
) -> InAppNotificationRead:
    result = await db.execute(
        select(InAppNotification).where(
            InAppNotification.id == notification_id,
            InAppNotification.tenant_id == tenant_id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notif)
    return InAppNotificationRead.model_validate(notif)


@router.post("/notifications/{recipient_id}/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    recipient_id: str,
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await db.execute(
        update(InAppNotification)
        .where(
            InAppNotification.tenant_id == tenant_id,
            InAppNotification.recipient_id == recipient_id,
            InAppNotification.is_read.is_(False),
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="In-App Notification Service",
    version=settings.VERSION,
    description="Real-time in-app notification persistence and delivery.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.SERVICE_NAME, version=settings.VERSION)
