from abc import ABC, abstractmethod
from typing import AsyncIterator, Callable, Awaitable
from .schemas import EventEnvelope


class EventBus(ABC):
    @abstractmethod
    async def publish(self, stream: str, event: EventEnvelope) -> str:
        """Publish event to stream; returns message ID."""

    @abstractmethod
    async def subscribe(
        self,
        stream: str,
        group: str,
        consumer: str,
        handler: Callable[[EventEnvelope], Awaitable[None]],
        batch_size: int = 10,
    ) -> None:
        """Subscribe to a stream and process events with handler."""

    @abstractmethod
    async def ack(self, stream: str, group: str, message_id: str) -> None:
        """Acknowledge processed message."""

    @abstractmethod
    async def close(self) -> None:
        """Release connections."""
