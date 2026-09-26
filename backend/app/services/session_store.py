"""
Persistent research state store.

Phase 1 implementation: one JSON file per session under `data/sessions/`.
This deliberately hides behind a small interface (get/save/list/delete) so
Phase 6+ can swap in Postgres/Mongo without touching agents or routes.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.models.schemas import ResearchSession


class SessionStore:
    def __init__(self, data_dir: Optional[str] = None):
        settings = get_settings()
        self._dir = Path(data_dir or settings.data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        # Guards concurrent writes to the same file from concurrent requests.
        self._lock = asyncio.Lock()

    def _path(self, session_id: str) -> Path:
        return self._dir / f"{session_id}.json"

    async def save(self, session: ResearchSession) -> None:
        session.touch()
        path = self._path(session.session_id)
        async with self._lock:
            path.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    async def get(self, session_id: str) -> Optional[ResearchSession]:
        path = self._path(session_id)
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
        return ResearchSession.model_validate_json(raw)

    async def list_sessions(self) -> list[ResearchSession]:
        sessions = []
        for path in sorted(self._dir.glob("*.json"), reverse=True):
            try:
                sessions.append(ResearchSession.model_validate_json(path.read_text(encoding="utf-8")))
            except Exception:
                continue  # skip corrupt/partial files rather than crash the listing
        return sessions

    async def delete(self, session_id: str) -> bool:
        path = self._path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False


# Process-wide singleton; fine for a single-instance Phase 1 deployment.
_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
