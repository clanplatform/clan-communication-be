from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.core.config import get_settings
from libs.communication_shared.schemas.base import HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: initialise connections
    yield
    # Shutdown: close connections


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    description="{{Service description}}",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
    )
