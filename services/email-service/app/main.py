from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from libs.communication_shared.schemas.base import HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="Email Service",
    version=settings.VERSION,
    description="Multi-provider email delivery service with SMTP/SendGrid/SES failover.",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
    )
