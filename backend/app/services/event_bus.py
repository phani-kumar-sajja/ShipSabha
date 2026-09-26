"""
Minimal in-memory event bus (Section 18: real-time agent activity).

Each research session gets its own set of asyncio.Queue subscribers. The
orchestrator publishes AgentEvent objects here; the WebSocket route
subscribes and forwards them to the connected frontend. Phase 2+ can
replace this with Redis pub/sub for multi-process deployments without
changing the publish()/subscribe() call sites.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict

from app.models.schemas import AgentEvent


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)

    async def publish(self, event: AgentEvent) -> None:
        for queue in list(self._subscribers.get(event.session_id, ())):
            await queue.put(event)

    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[session_id].add(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        self._subscribers[session_id].discard(queue)


_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
