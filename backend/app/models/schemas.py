"""
Structured data contracts for the research workflow.

These mirror the internal representation described in the product spec
(Section 3: input processing, Section 14: research state management) and
are the single source of truth shared by every stage/agent and by the API
layer. The frontend's src/types/research.ts must be kept in sync with this
file.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

class ResearchStage(str, Enum):
    """The full pipeline from the spec. Phase 1 implements up through
    domain validation; later stages exist now so state/events have a
    stable shape as they come online."""
    SUBMITTED = "submitted"
    DOMAIN_VALIDATION = "domain_validation"
    RESEARCH_PLANNING = "research_planning"
    LITERATURE_REVIEW = "literature_review"
    EXISTING_APPROACHES = "existing_approaches"
    RESEARCH_GAP = "research_gap"
    HYPOTHESIS_FORMATION = "hypothesis_formation"
    EXPERIMENT_DESIGN = "experiment_design"
    EXPERIMENT_EXECUTION = "experiment_execution"
    RESULT_ANALYSIS = "result_analysis"
    COMPARISON = "comparison"
    HYPOTHESIS_REFINEMENT = "hypothesis_refinement"
    FINDINGS = "findings"
    REPORT = "report"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


class SessionStatus(str, Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    REJECTED = "rejected"  # domain validation failed
    COMPLETED = "completed"
    ERROR = "error"


# --------------------------------------------------------------------------
# Input (Section 3)
# --------------------------------------------------------------------------

class ResearchQuestionInput(BaseModel):
    research_question: str = Field(..., min_length=8, max_length=4000)
    constraints: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    preferred_language: Optional[str] = None
    computational_constraints: Optional[str] = None
    research_objectives: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Domain validation (Section 2)
# --------------------------------------------------------------------------

class DomainValidationResult(BaseModel):
    is_cse_related: bool
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    suggested_reformulation: Optional[str] = None


# --------------------------------------------------------------------------
# Stage progress record (drives Section 17/18 UI + events)
# --------------------------------------------------------------------------

class StageRecord(BaseModel):
    stage: ResearchStage
    status: StageStatus = StageStatus.PENDING
    message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


# --------------------------------------------------------------------------
# Streaming event envelope (Section 18)
# --------------------------------------------------------------------------

class AgentEvent(BaseModel):
    type: str
    session_id: str
    stage: Optional[ResearchStage] = None
    status: Optional[StageStatus] = None
    message: str = ""
    data: dict = Field(default_factory=dict)
    timestamp: str = Field(default_factory=_now)


# --------------------------------------------------------------------------
# Full research session state (Section 14)
# --------------------------------------------------------------------------

class ResearchSession(BaseModel):
    session_id: str = Field(default_factory=lambda: _new_id("sess"))
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)

    research_question: str
    constraints: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    preferred_language: Optional[str] = None
    computational_constraints: Optional[str] = None
    research_objectives: list[str] = Field(default_factory=list)

    domain: Optional[str] = None
    subdomain: Optional[str] = None
    domain_validation: Optional[DomainValidationResult] = None

    status: SessionStatus = SessionStatus.INITIALIZED
    current_stage: ResearchStage = ResearchStage.SUBMITTED
    stages: list[StageRecord] = Field(
        default_factory=lambda: [StageRecord(stage=s) for s in ResearchStage]
    )

    # Populated by later phases; present now so the shape is stable.
    literature: list[dict] = Field(default_factory=list)
    existing_approaches: list[dict] = Field(default_factory=list)
    research_gaps: list[dict] = Field(default_factory=list)
    hypotheses: list[dict] = Field(default_factory=list)
    experiments: list[dict] = Field(default_factory=list)
    results: list[dict] = Field(default_factory=list)
    comparisons: list[dict] = Field(default_factory=list)
    findings: list[dict] = Field(default_factory=list)
    artifacts: list[dict] = Field(default_factory=list)

    def touch(self) -> None:
        self.updated_at = _now()

    def get_stage(self, stage: ResearchStage) -> StageRecord:
        for record in self.stages:
            if record.stage == stage:
                return record
        raise KeyError(stage)

    def set_stage_status(
        self,
        stage: ResearchStage,
        status: StageStatus,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ) -> StageRecord:
        record = self.get_stage(stage)
        record.status = status
        if message is not None:
            record.message = message
        if error is not None:
            record.error = error
        if status == StageStatus.RUNNING and record.started_at is None:
            record.started_at = _now()
        if status in (StageStatus.COMPLETE, StageStatus.FAILED, StageStatus.SKIPPED):
            record.completed_at = _now()
        self.current_stage = stage
        self.touch()
        return record
