# Agentic CSE Research Assistant

An autonomous research-workflow platform for Computer Science & Engineering:
a user submits a research question, the system validates it's in-scope,
then (in later phases) runs literature review, gap analysis, hypothesis
formation, experiment execution, and report generation as a stateful,
observable, interruptible agentic pipeline.

This repo currently implements **Phase 1** of the build plan:

- Project structure (this layout)
- Backend: FastAPI service, persistent JSON-backed session state,
  streaming events over WebSocket
- Frontend: React + TypeScript dashboard with an intake form and a live
  progress panel
- Research session creation
- CSE domain validation (semantic, LLM-backed Domain Validator agent)

The pipeline intentionally **stops right after domain validation** —
research planning, literature review, experiment execution, etc. are
later phases (see "Roadmap" below) and are represented in the data model
now (`ResearchStage` enum, event types) so the UI and API contracts don't
change shape as they come online.

## Architecture

```
frontend/   React + TypeScript dashboard (Vite), talks to the backend over
            REST (create/list sessions) and WebSocket (live stage events)
backend/    FastAPI service
  app/core/         configuration (env vars, no hardcoded secrets)
  app/models/       Pydantic schemas = the shared research-state contract
  app/services/
    llm_client.py        thin Anthropic API wrapper (all agents call through this)
    domain_validator.py  Domain Validator agent (Section 2 semantic CSE check)
    orchestrator.py       Agent Orchestrator: runs stages, updates state, emits events
    session_store.py      JSON-file-backed persistent research state (swappable for a real DB)
    event_bus.py           in-memory pub/sub -> WebSocket streaming
  app/api/routes/
    sessions.py    POST/GET/DELETE /api/sessions
    ws.py          GET /ws/sessions/{id} (WebSocket event stream)
  tests/           pytest + pytest-asyncio, LLM calls mocked (no network needed to test)
```

## Running locally

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

Run tests (no API key required — the LLM call is mocked):

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` and `/ws`
to the backend on port 8000 (see `vite.config.ts`).

## Environment variables

See `backend/.env.example`. Required: `ANTHROPIC_API_KEY`. Everything
else has a sane local-dev default. Never commit a real `.env` file.

## Roadmap (later phases, not yet implemented)

- **Phase 2** — richer orchestrator state machine, pause/resume/stop controls
- **Phase 3** — Literature Review agent (web/academic search + structured
  paper extraction), Existing Approaches agent, Research Gap agent
- **Phase 4** — Hypothesis agent, Experiment Designer, Code Generation agent
- **Phase 5** — sandboxed Experiment Execution agent (subprocess/container
  isolation), Data Analysis agent, plots/tables
- **Phase 6** — Comparison-with-prior-work agent, Research Critic gate,
  iterative hypothesis-refinement loop
- **Phase 7** — Findings/report generator with Markdown/LaTeX/PDF export,
  full artifact management under `research_session/...`

## Research-integrity rules baked into the design

- The system never claims an experiment ran if it didn't (Section 23) —
  `orchestrator.py` only marks a stage `complete` after the underlying
  call actually returns; failures are written into `StageRecord.error`
  and streamed to the UI, never swallowed.
- `domain_validator.py` returns a confidence score and rationale rather
  than a bare boolean, so the UI can show *why* a question was accepted
  or rejected instead of a black-box verdict.
- `session_store.py` persists the full session as structured state, not
  just a final answer, so every stage's provenance survives a restart.
