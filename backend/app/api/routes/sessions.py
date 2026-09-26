from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models.schemas import ResearchQuestionInput, ResearchSession
from app.services.orchestrator import run_intake_and_validation
from app.services.session_store import get_session_store

logger = logging.getLogger("research_assistant.api.sessions")
router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=ResearchSession, status_code=201)
async def create_session(payload: ResearchQuestionInput, background_tasks: BackgroundTasks):
    """Creates a research session and kicks off intake + CSE domain
    validation in the background. Poll GET /api/sessions/{id} or connect
    to /ws/sessions/{id} for live progress."""
    store = get_session_store()

    session = ResearchSession(
        research_question=payload.research_question,
        constraints=payload.constraints,
        datasets=payload.datasets,
        preferred_language=payload.preferred_language,
        computational_constraints=payload.computational_constraints,
        research_objectives=payload.research_objectives,
    )
    await store.save(session)

    async def _run():
        try:
            await run_intake_and_validation(session)
        except Exception:  # noqa: BLE001 - last-resort guard, never crash silently (Section 22)
            logger.exception("Unhandled orchestrator failure for session %s", session.session_id)

    background_tasks.add_task(_run)
    return session


@router.get("", response_model=list[ResearchSession])
async def list_sessions():
    store = get_session_store()
    return await store.list_sessions()


@router.get("/{session_id}", response_model=ResearchSession)
async def get_session(session_id: str):
    store = get_session_store()
    session = await store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    store = get_session_store()
    deleted = await store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
