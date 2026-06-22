"""
Lightweight WebSocket service for real-time notification delivery.
Maintains per-tenant, per-recipient connection pools backed by Redis pub/sub.
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "websocket-service"
    VERSION: str = "1.0.0"
    REDIS_URL: str = "redis://localhost:6379/0"
    PORT: int = 8006

settings = Settings()

# ---------------------------------------------------------------------------
# Connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self) -> None:
        # tenant_id -> recipient_id -> set of WebSocket connections
        self._connections: dict[str, dict[str, set[WebSocket]]] = defaultdict(
            lambda: defaultdict(set)
        )

    async def connect(self, tenant_id: str, recipient_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[tenant_id][recipient_id].add(ws)
        logger.info("WS connected: tenant=%s recipient=%s", tenant_id, recipient_id)

    def disconnect(self, tenant_id: str, recipient_id: str, ws: WebSocket) -> None:
        self._connections[tenant_id][recipient_id].discard(ws)
        if not self._connections[tenant_id][recipient_id]:
            del self._connections[tenant_id][recipient_id]
        logger.info("WS disconnected: tenant=%s recipient=%s", tenant_id, recipient_id)

    async def send_to_recipient(
        self, tenant_id: str, recipient_id: str, message: dict
    ) -> int:
        conns = self._connections.get(tenant_id, {}).get(recipient_id, set())
        sent = 0
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
                sent += 1
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(tenant_id, recipient_id, ws)
        return sent

    async def broadcast_to_tenant(self, tenant_id: str, message: dict) -> int:
        total = 0
        for recipient_id in list(self._connections.get(tenant_id, {}).keys()):
            total += await self.send_to_recipient(tenant_id, recipient_id, message)
        return total


manager = ConnectionManager()

# ---------------------------------------------------------------------------
# Redis subscriber (forwards Redis pub/sub messages to WebSocket clients)
# ---------------------------------------------------------------------------

_redis: aioredis.Redis | None = None
_subscriber_task: asyncio.Task | None = None


async def redis_subscriber() -> None:
    global _redis
    assert _redis is not None
    pubsub = _redis.pubsub()
    await pubsub.psubscribe("ws:*")
    async for message in pubsub.listen():
        if message["type"] != "pmessage":
            continue
        try:
            channel: str = message["channel"]  # ws:{tenant_id}:{recipient_id}
            parts = channel.split(":", 2)
            if len(parts) < 3:
                continue
            _, tenant_id, recipient_id = parts
            data = json.loads(message["data"])
            await manager.send_to_recipient(tenant_id, recipient_id, data)
        except Exception:
            logger.exception("Redis subscriber error")


# ---------------------------------------------------------------------------
# App lifecycle & HTTP endpoints
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _redis, _subscriber_task
    _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    _subscriber_task = asyncio.create_task(redis_subscriber())
    yield
    _subscriber_task.cancel()
    if _redis:
        await _redis.aclose()


app = FastAPI(
    title="WebSocket Service",
    version=settings.VERSION,
    description="Real-time WebSocket gateway for multi-tenant notification delivery.",
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

# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws/{tenant_id}/{recipient_id}")
async def websocket_endpoint(
    websocket: WebSocket, tenant_id: str, recipient_id: str
) -> None:
    await manager.connect(tenant_id, recipient_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo heartbeat pings back as pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(tenant_id, recipient_id, websocket)


# ---------------------------------------------------------------------------
# Internal broadcast endpoint (called by other services)
# ---------------------------------------------------------------------------

class BroadcastRequest(BaseModel):
    tenant_id: str
    recipient_id: str
    event: str
    data: dict


@app.post("/broadcast", status_code=status.HTTP_202_ACCEPTED)
async def broadcast(request: BroadcastRequest) -> dict:
    message = {"event": request.event, "data": request.data}
    # Publish to Redis for multi-instance fan-out
    if _redis:
        channel = f"ws:{request.tenant_id}:{request.recipient_id}"
        await _redis.publish(channel, json.dumps(message))
    sent = await manager.send_to_recipient(request.tenant_id, request.recipient_id, message)
    return {"sent_to": sent}


@app.get("/health")
async def health() -> dict:
    redis_ok = False
    if _redis:
        try:
            await _redis.ping()
            redis_ok = True
        except Exception:
            pass
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "redis": "ok" if redis_ok else "error",
    }
