from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI
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


# --- CORS (env-driven via CORS_ORIGINS) ------------------------------------
# Authoritative CORS is the API gateway (Envoy). This block only applies while
# the service is exposed directly (Render/nginx ingress). Origins come from the
# CORS_ORIGINS env var (JSON list or comma-separated). Empty => no CORS (prod
# default-deny); dev falls back to localhost.
import os as _os
import json as _json
from fastapi.middleware.cors import CORSMiddleware as _CORSMiddleware


def _clan_cors_origins() -> list:
    raw = (_os.getenv("CORS_ORIGINS") or "").strip()
    if raw.startswith("["):
        try:
            return [str(o).strip() for o in _json.loads(raw) if str(o).strip()]
        except Exception:
            return []
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins and _os.getenv("ENVIRONMENT", "development").lower().startswith(("dev", "local")):
        origins = ["http://localhost:3000", "http://localhost:8080"]
    return origins


_clan_origins = _clan_cors_origins()
if _clan_origins:
    app.add_middleware(
        _CORSMiddleware,
        allow_origins=_clan_origins,
        allow_credentials="*" not in _clan_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
# ---------------------------------------------------------------------------

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
