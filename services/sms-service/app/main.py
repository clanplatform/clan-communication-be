from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi import APIRouter

from app.core.config import get_settings
from app.api.v1.endpoints.sms import router as sms_router
from libs.communication_shared.schemas.base import HealthResponse

settings = get_settings()

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(sms_router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="SMS Service",
    version=settings.VERSION,
    description="Multi-provider SMS delivery service (Twilio/Vonage/SNS).",
    lifespan=lifespan,
)
app.include_router(api_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.SERVICE_NAME, version=settings.VERSION)
