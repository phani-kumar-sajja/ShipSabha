from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.event_bus import get_event_bus
from app.services.session_store import get_session_store

logger = logging.getLogger("research_assistant.api.ws")
router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def session_events(websocket: WebSocket, session_id: str):
    """Streams AgentEvents for one research session so the dashboard can
    update live without polling or blocking on long-running stages."""
    await websocket.accept()

    store = get_session_store()
    session = await store.get(session_id)
    if session is None:
        await websocket.send_json({"type": "error", "message": "Session not found."})
        await websocket.close(code=4404)
        return

    # Send current state immediately so a client that connects mid-run
    # (or reconnects) doesn't have to wait for the next event to render.
    await websocket.send_json({"type": "snapshot", "session": session.model_dump(mode="json")})

    bus = get_event_bus()
    queue = bus.subscribe(session_id)
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event.model_dump(mode="json"))
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        logger.exception("WebSocket stream error for session %s", session_id)
    finally:
        bus.unsubscribe(session_id, queue)
