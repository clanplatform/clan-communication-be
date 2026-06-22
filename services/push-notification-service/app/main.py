from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.push import SendPushRequest, PushLogRead
from app.services.push_provider import PushProviderService
from libs.communication_shared.schemas.base import HealthResponse

settings = get_settings()

router = APIRouter(prefix="/api/v1/send", tags=["push"])


@router.post("", response_model=PushLogRead, status_code=status.HTTP_202_ACCEPTED)
async def send_push(request: SendPushRequest, db: AsyncSession = Depends(get_db)) -> PushLogRead:
    svc = PushProviderService(db)
    log = await svc.send(
        notification_id=request.notification_id,
        tenant_id=request.tenant_id,
        device_token=request.device_token,
        platform=request.platform,
        body=request.body,
        title=request.title,
        data=request.data,
    )
    return PushLogRead.model_validate(log)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="Push Notification Service",
    version=settings.VERSION,
    description="FCM/APNS push notification delivery.",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.SERVICE_NAME, version=settings.VERSION)
