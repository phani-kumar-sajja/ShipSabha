"""
Tests for Phase 1: session intake + CSE domain validation.

The Anthropic call is monkeypatched so tests run offline/deterministically
and never hit the network or require a real API key.
"""
from __future__ import annotations

import asyncio
import tempfile

import pytest

from app.models.schemas import DomainValidationResult, ResearchSession, SessionStatus
from app.services import domain_validator, orchestrator
from app.services.session_store import SessionStore


@pytest.fixture
def tmp_store(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        store = SessionStore(data_dir=tmp)
        monkeypatch.setattr("app.services.orchestrator.get_session_store", lambda: store)
        yield store


@pytest.mark.asyncio
async def test_cse_question_is_accepted(tmp_store, monkeypatch):
    async def fake_validate(question: str) -> DomainValidationResult:
        return DomainValidationResult(
            is_cse_related=True,
            domain="Machine Learning",
            subdomain="Federated Learning",
            confidence=0.95,
            rationale="Concerns distributed model training, a core ML/systems topic.",
        )

    monkeypatch.setattr(orchestrator, "validate_domain", fake_validate)

    session = ResearchSession(research_question="How does client drift affect federated learning convergence?")
    result = await orchestrator.run_intake_and_validation(session)

    assert result.domain == "Machine Learning"
    assert result.status == SessionStatus.PAUSED
    assert result.domain_validation.is_cse_related is True


@pytest.mark.asyncio
async def test_non_cse_question_is_rejected(tmp_store, monkeypatch):
    async def fake_validate(question: str) -> DomainValidationResult:
        return DomainValidationResult(
            is_cse_related=False,
            domain=None,
            subdomain=None,
            confidence=0.9,
            rationale="This is a question about 18th-century political history, not CSE.",
            suggested_reformulation=None,
        )

    monkeypatch.setattr(orchestrator, "validate_domain", fake_validate)

    session = ResearchSession(research_question="What caused the French Revolution?")
    result = await orchestrator.run_intake_and_validation(session)

    assert result.status == SessionStatus.REJECTED
    assert result.domain_validation.is_cse_related is False


@pytest.mark.asyncio
async def test_llm_failure_is_recorded_not_swallowed(tmp_store, monkeypatch):
    async def failing_validate(question: str):
        raise domain_validator.LLMError("simulated transport failure")

    monkeypatch.setattr(orchestrator, "validate_domain", failing_validate)

    session = ResearchSession(research_question="Does attention scale sub-quadratically with sequence length?")
    result = await orchestrator.run_intake_and_validation(session)

    assert result.status == SessionStatus.ERROR
    failed_stage = result.get_stage(result.stages[1].stage)  # domain_validation is stages[1]
    assert failed_stage.error is not None
