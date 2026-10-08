# DECISIONS.md

All decisions about architecture (ADR log).

## ADR-001 — LangGraph for orchestration

- **Status:** Accepted
- **Context:** Review is a multi-step workflow with branching (`plan` decides which
  specialists run), shared state and the need for per-node tracing/checkpointing.
- **Decision:** Use LangGraph nodes + a shared `ReviewState` TypedDict.
- **Consequences:** Checkpointing and LangSmith spans come for free; workflow is visualizable;
  we accept the framework dependency.

## ADR-002 — Supervisor + specialist multi-agent design

- **Status:** Accepted
- **Context:** One monolithic prompt dilutes focus across style, security, bugs and tests.
- **Decision:** A supervisor plans; five specialists each own one concern and return
  `list[Finding]`.
- **Consequences:** Prompts stay small and testable; failures are isolated per specialist;
  more nodes to trace and cost per run.

## ADR-003 — ChromaDB as vector memory

- **Status:** Accepted
- **Context:** Conventions, past reviews and docs must be retrievable locally with no
  managed service dependency.
- **Decision:** ChromaDB with persist dir `CHROMA_PATH`, three collections
  (`project_conventions`, `past_reviews`, `codebase_docs`).
- **Consequences:** Simple single-process deployment; embedding cost on ingestion; swapping to
  a hosted store later is a config change.

## ADR-004 — LangSmith for observability and eval

- **Status:** Accepted
- **Context:** Agent runs are non-deterministic enough that "it looked fine" is not a
  quality signal.
- **Decision:** One trace per review run, one span per node, prompt versions tracked, eval
  datasets replayed on prompt change.
- **Consequences:** Debugging becomes evidence-based; requires `LANGSMITH_API_KEY` for full
  value (optional, tracing off without it).

## ADR-005 — Docker as the delivery unit

- **Status:** Accepted
- **Context:** Must run identically on a laptop, in CI and as a service.
- **Decision:** One image; CLI, CI worker and webhook service are entrypoints into it.
- **Consequences:** Reproducibility; image size and build time become a concern to watch.

## ADR-006 — Env-var (12-factor) configuration

- **Status:** Accepted
- **Context:** Same image must work across local/CI/service without code changes.
- **Decision:** All config from environment variables (`SPECIFICATION.md §2`), no config
  files baked into the image.
- **Consequences:** Simple, testable, secret-friendly; many knobs live in the orchestrator.

## ADR-007 — Pydantic data contracts

- **Status:** Accepted
- **Context:** Findings must be validated before aggregation and serialization.
- **Decision:** `Finding` and `ReviewReport` are pydantic `BaseModel`s; state carries
  `list[Finding]`.
- **Consequences:** Validation errors surface early; JSON artifact schema is derived, not
  hand-written.

## ADR-008 — Exit codes as the CI contract

- **Status:** Accepted
- **Context:** CI needs a machine-readable verdict.
- **Decision:** `0` clean, `1` blocker/major present, `2` run failure.
- **Consequences:** Pipelines can gate on findings without parsing markdown; must never
  collapse `1` and `2` into the same signal.

## Decision log rules

New decisions append as ADR-NNN with Status `Proposed → Accepted | Rejected | Superseded`.
Reversing a decision requires a new ADR referencing the old one.
