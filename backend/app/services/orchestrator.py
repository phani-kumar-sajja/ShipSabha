"""
Agent Orchestrator (Section 15/25).

Phase 1 scope: run intake and CSE domain validation, updating persistent
session state and emitting streaming events at each step. Later phases
add a stage here per new agent (literature review, hypothesis, ...)
without changing how sessions are created or how the frontend consumes
events -- new ResearchStage values already exist in the schema so the
progress UI has stable ground to render against as stages come online.
"""
from __future__ import annotations

import logging

from app.models.schemas import (
    AgentEvent,
    ResearchSession,
    ResearchStage,
    SessionStatus,
    StageStatus,
)
from app.services.domain_validator import validate_domain
from app.services.event_bus import get_event_bus
from app.services.llm_client import LLMError
from app.services.session_store import get_session_store

logger = logging.getLogger("research_assistant.orchestrator")


async def _emit(session: ResearchSession, event_type: str, message: str = "", **data) -> None:
    await get_event_bus().publish(
        AgentEvent(
            type=event_type,
            session_id=session.session_id,
            stage=session.current_stage,
            status=session.get_stage(session.current_stage).status,
            message=message,
            data=data,
        )
    )


async def run_intake_and_validation(session: ResearchSession) -> ResearchSession:
    """Runs Stage 0 (submitted) -> Domain Validation (Section 2) and
    persists/streams progress throughout. This is the Phase 1 entry point
    invoked right after a session is created."""
    store = get_session_store()

    session.status = SessionStatus.RUNNING
    session.set_stage_status(ResearchStage.SUBMITTED, StageStatus.COMPLETE, "Research question received.")
    await store.save(session)
    await _emit(session, "research_started", "Research question received.")

    session.set_stage_status(
        ResearchStage.DOMAIN_VALIDATION, StageStatus.RUNNING, "Analyzing whether this question is CSE-related."
    )
    await store.save(session)
    await _emit(session, "stage_update", "Validating research domain (CSE scope check)...")

    try:
        result = await validate_domain(session.research_question)
    except LLMError as exc:
        session.set_stage_status(
            ResearchStage.DOMAIN_VALIDATION,
            StageStatus.FAILED,
            error=str(exc),
        )
        session.status = SessionStatus.ERROR
        await store.save(session)
        await _emit(session, "domain_validation_error", str(exc))
        logger.error("Domain validation failed for session %s: %s", session.session_id, exc)
        return session

    session.domain_validation = result

    if not result.is_cse_related:
        session.set_stage_status(
            ResearchStage.DOMAIN_VALIDATION,
            StageStatus.FAILED,
            message="Question is not substantially related to Computer Science and Engineering.",
        )
        session.status = SessionStatus.REJECTED
        await store.save(session)
        await _emit(
            session,
            "domain_rejected",
            "This system is restricted to Computer Science and Engineering research questions.",
            rationale=result.rationale,
            suggested_reformulation=result.suggested_reformulation,
        )
        return session

    session.domain = result.domain
    session.subdomain = result.subdomain
    session.set_stage_status(
        ResearchStage.DOMAIN_VALIDATION,
        StageStatus.COMPLETE,
        message=f"Confirmed CSE domain: {result.domain or 'General CSE'}"
        + (f" / {result.subdomain}" if result.subdomain else ""),
    )
    await store.save(session)
    await _emit(
        session,
        "domain_validated",
        f"Domain confirmed: {result.domain}",
        domain=result.domain,
        subdomain=result.subdomain,
        confidence=result.confidence,
    )

    # Next stage (Research Planning) is marked pending here; Phase 3 wires
    # in the actual planning agent. We stop the automated run at the edge
    # of what Phase 1 implements rather than silently no-op'ing forward.
    session.status = SessionStatus.PAUSED
    session.current_stage = ResearchStage.RESEARCH_PLANNING
    await store.save(session)
    await _emit(
        session,
        "stage_update",
        "Domain validated. Research planning is not yet implemented (Phase 3) -- session paused here.",
    )
    return session
