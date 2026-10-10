# CHANGELOG.md

Release history. Format follows [Keep a Changelog](https://keepachangelog.com/);
versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added

- Graph implementation (T-004 … T-008): `ReviewState` (`app/state.py`), node
  implementations in `app/nodes.py` wired linearly via LangGraph —
  `start → plan → context_retriever → specialists → aggregate → report`.
  `plan` fallback = run all specialists; specialists retry ×2 then record into
  `ReviewState.errors`; `aggregate` never fails; `report` aborts on failure.
  Temperature `0` specialists / `0.2` summarizer (`app/prompts.py`,
  `app/llm.py`), untrusted output coerced by `app/parsing.py`.
- Memory layer (T-009, T-010): ChromaDB collections `project_conventions`,
  `past_reviews`, `codebase_docs`; `python -m app.ingest <repo>`
  (`app/ingest.py`, `app/memory.py`); `context_retriever` degrades to empty
  context + recorded error, ≤ 8 chunks.
- LangSmith tracing (T-011): `app/tracing.py` — one trace per run, one span per
  node, `trace_url` embedded in the report; tracing failures never break a run.
- CLI (T-003): `python index.py review <diff|->` reads file or stdin, emits
  markdown + `review_report.json`, exit codes `0 | 1 | 2`
  (`SPECIFICATION.md §7`), `--help`, per-file splitting for diffs >
  `MAX_DIFF_LINES` (`app/diff.py`, `app/runner.py`).
- Docker image (T-012): `Dockerfile` + `.dockerignore` — non-root, no secrets
  in layers, single entrypoint for all shapes; `fixtures/clean.patch` and
  `fixtures/blocker.patch` for smoke runs.
- CI (T-013): `.github/workflows/ci.yml` (pytest + image build/smoke) and
  `review.yml` (PR review worker: exit 1 → comment + fail, exit 2 →
  infrastructure failure).
- Tests restructured to `tests/contract`, `tests/graph`, `tests/unit`
  (`TESTING.md` commands); 125 tests total.
- Config loader `app/config.py` with validation and fail-fast `ConfigError`
  (exit code `2`); `app/nodes.py` node registry; entry point prints model + node list
  (`STEPS.md §1`), covered by 15 tests.
- Data contracts `app/models.py` — `Finding` and `ReviewReport` pydantic models with
  severity/category literals and `confidence` bounds (`STEPS.md §2`), 17 contract tests.
- `requirements.txt`, `.env.example`, `.gitignore` (`STEPS.md §0`).
- Complete documentation set — all files listed in `FILES.md` / `ALL.md` docs map.
- Task breakdown `TASKS.md` (T-001 … T-014) mapped to `ROADMAP.md` phases.
- Process docs: `CONTRIBUTION.md`, `HUMAN.md`, `CONVERSATION.md`.
- Operations docs: `DEPLOYMENTS.md`, `OPERATIONS.md`, `TESTING.md`,
  `TROUBLESHOOTING.md`.
- Policy docs: `SECURITY.md`, `PRIVACY.md`.
- Meta docs: `FILES.md`, `CHANGELOG.md`.

## [0.1.0] — M0 Skeleton

### Added

- Repository skeleton with `index.py` entry point.
- Vision, milestones, roadmap, backlogs and principles.
- Architecture, specification and requirements: graph nodes, `ReviewState`, `Finding` /
  `ReviewReport` contracts, configuration table, exit codes `0 | 1 | 2`.
- ADR log (`DECISIONS.md`) — ADR-001 … ADR-008.

### Known gaps

- No graph, no memory, no tracing, no Docker image, no `review <diff>` CLI yet
  (`BACKLOGS.md` → Now).

## Versioning rules

- **Major** — a contract changes (`Finding`, `ReviewReport`, exit codes) or a documented
  deployment shape is removed.
- **Minor** — a node, specialist, backlog capability or doc section is added.
- **Patch** — prompt tuning, docs fixes, bug fixes with no contract change.
- Every release updates `FILES.md` if files moved, and `MILESTONES.md` if a milestone
  closed.
