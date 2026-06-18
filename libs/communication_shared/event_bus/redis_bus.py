import json
import asyncio
import logging
from typing import Callable, Awaitable

import redis.asyncio as aioredis

from .base import EventBus
from .schemas import EventEnvelope

logger = logging.getLogger(__name__)


class RedisEventBus(EventBus):
    def __init__(self, redis_url: str, max_len: int = 10_000) -> None:
        self._url = redis_url
        self._max_len = max_len
        self._client: aioredis.Redis | None = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )
        return self._client

    async def publish(self, stream: str, event: EventEnvelope) -> str:
        client = await self._get_client()
        payload = {"data": event.model_dump_json()}
        msg_id = await client.xadd(stream, payload, maxlen=self._max_len, approximate=True)
        logger.debug("Published event %s to %s (id=%s)", event.event_type, stream, msg_id)
        return msg_id

    async def _ensure_group(self, client: aioredis.Redis, stream: str, group: str) -> None:
        try:
            await client.xgroup_create(stream, group, id="0", mkstream=True)
        except aioredis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def subscribe(
        self,
        stream: str,
        group: str,
        consumer: str,
        handler: Callable[[EventEnvelope], Awaitable[None]],
        batch_size: int = 10,
    ) -> None:
        client = await self._get_client()
        await self._ensure_group(client, stream, group)

        while True:
            try:
                messages = await client.xreadgroup(
                    group, consumer, {stream: ">"}, count=batch_size, block=2000
                )
                for _, entries in messages or []:
                    for msg_id, fields in entries:
                        try:
                            event = EventEnvelope.model_validate_json(fields["data"])
                            await handler(event)
                            await self.ack(stream, group, msg_id)
                        except Exception:
                            logger.exception("Failed processing message %s", msg_id)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Event bus subscriber error; retrying in 2s")
                await asyncio.sleep(2)

    async def ack(self, stream: str, group: str, message_id: str) -> None:
        client = await self._get_client()
        await client.xack(stream, group, message_id)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
