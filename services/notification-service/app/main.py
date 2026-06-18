from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis

from app.api.v1.router import api_router
from app.core.config import get_settings
from libs.communication_shared.schemas.base import HealthResponse

settings = get_settings()

_redis_client: aioredis.Redis | None = None
_http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _redis_client, _http_client
    _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    _http_client = httpx.AsyncClient(timeout=10.0)
    yield
    if _redis_client:
        await _redis_client.aclose()
    if _http_client:
        await _http_client.aclose()


app = FastAPI(
    title="Notification Service",
    version=settings.VERSION,
    description="Core notification orchestration service for multi-tenant SaaS communication platform.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    checks: dict[str, str] = {}
    if _redis_client:
        try:
            await _redis_client.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "error"
    return HealthResponse(
        status="ok",
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
        checks=checks,
    )
