from contextlib import asynccontextmanager
from typing import AsyncIterator, Any

from fastapi import FastAPI, APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.whatsapp_log import WhatsAppLog
from app.services.whatsapp_provider import WhatsAppProviderService
from libs.communication_shared.schemas.base import HealthResponse

settings = get_settings()


class SendWhatsAppRequest(BaseModel):
    notification_id: str
    tenant_id: str
    recipient_id: str
    to_number: str = Field(..., pattern=r"^\+?[1-9]\d{7,14}$")
    body: str = Field(..., min_length=1, max_length=4096)
    media_url: str | None = None


class WhatsAppLogRead(BaseModel):
    id: str
    tenant_id: str
    notification_id: str
    to_number: str
    body: str
    provider: str
    provider_message_id: str | None
    status: str
    retry_count: int

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/api/v1/send", tags=["whatsapp"])


@router.post("", response_model=WhatsAppLogRead, status_code=status.HTTP_202_ACCEPTED)
async def send_whatsapp(
    request: SendWhatsAppRequest,
    db: AsyncSession = Depends(get_db),
) -> WhatsAppLogRead:
    svc = WhatsAppProviderService(db)
    log = await svc.send(
        notification_id=request.notification_id,
        tenant_id=request.tenant_id,
        to_number=request.to_number,
        body=request.body,
        media_url=request.media_url,
    )
    return WhatsAppLogRead.model_validate(log)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="WhatsApp Service",
    version=settings.VERSION,
    description="WhatsApp message delivery via WebJS worker and Meta Business API.",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.SERVICE_NAME, version=settings.VERSION)
