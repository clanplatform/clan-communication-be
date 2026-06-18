from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.deps import get_tenant_id, verify_api_key
from app.schemas.notification import (
    NotificationCreate,
    NotificationRead,
    NotificationUpdate,
    BulkNotificationCreate,
)
from app.services.notification_service import NotificationService
from app.services.dispatcher import ChannelDispatcher
from app.services.template_service import TemplateService
from app.core.config import get_settings
from libs.communication_shared.schemas.base import PaginatedResponse
from libs.communication_shared.exceptions import (
    RateLimitError,
    TemplateNotFoundError,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])
settings = get_settings()


def _build_service(db: AsyncSession) -> NotificationService:
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    http_client = httpx.AsyncClient()
    dispatcher = ChannelDispatcher(http_client)
    template_svc = TemplateService(db)
    return NotificationService(db, redis_client, dispatcher, template_svc)


@router.post("", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    svc = _build_service(db)
    try:
        notif = await svc.create(tenant_id, payload)
    except RateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)
    except TemplateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return NotificationRead.model_validate(notif)


@router.post("/bulk", response_model=list[NotificationRead], status_code=status.HTTP_201_CREATED)
async def bulk_create_notifications(
    payload: BulkNotificationCreate,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationRead]:
    svc = _build_service(db)
    try:
        notifications = await svc.bulk_create(tenant_id, payload.notifications)
    except RateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)
    return [NotificationRead.model_validate(n) for n in notifications]


@router.get("/{notification_id}", response_model=NotificationRead)
async def get_notification(
    notification_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    svc = _build_service(db)
    notif = await svc.get(tenant_id, notification_id)
    if notif is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationRead.model_validate(notif)


@router.get("/recipient/{recipient_id}", response_model=PaginatedResponse[NotificationRead])
async def list_by_recipient(
    recipient_id: str,
    page: int = 1,
    page_size: int = 20,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[NotificationRead]:
    svc = _build_service(db)
    items, total = await svc.list_by_recipient(tenant_id, recipient_id, page, page_size)
    return PaginatedResponse(
        items=[NotificationRead.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.patch("/{notification_id}/status", response_model=NotificationRead)
async def update_notification_status(
    notification_id: str,
    payload: NotificationUpdate,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    svc = _build_service(db)
    notif = await svc.update_status(tenant_id, notification_id, payload)
    if notif is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationRead.model_validate(notif)
