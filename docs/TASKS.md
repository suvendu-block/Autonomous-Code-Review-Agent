# TASKS.md

Executable breakdown of the roadmap.

Each task is small, verifiable and maps to exactly one backlog item. Status: `todo` → `doing`
→ `done`. A task is done when its exit criteria pass and the related docs are updated.

## T-001 — Config loader

- **Phase:** 1 · **Backlog:** Now (P0)
- Read all `SPECIFICATION.md §2` variables from the environment.
- Validate: required vars present, `REVIEW_SEVERITY` in `strict | normal | lenient`,
  `MAX_DIFF_LINES` a positive int.
- Exit: `python index.py` prints model id + node list; missing `LLM_API_KEY` exits `2` with an
  explicit message.

## T-002 — Data contracts

- **Phase:** 1 · **Backlog:** Now (P0)
- Add `Finding` and `ReviewReport` pydantic models (`SPECIFICATION.md §3`).
- Exit: models importable; validation tests cover severity/category literals and
  `confidence` bounds `0..1`.

## T-003 — CLI skeleton

- **Phase:** 1 · **Backlog:** Now (P0)
- `review <diff>` reads a diff from file or stdin, emits markdown + `review_report.json`.
- Exit: exit codes `0 | 1 | 2` match `SPECIFICATION.md §7`; empty diff → explicit error, `2`.

## T-004 — `ReviewState` + `start` node

- **Phase:** 2 · **Backlog:** Now (P0)
- Define the `ReviewState` TypedDict (`ARCHITECTURE.md`); `start` loads diff and file list.
- Exit: state carries `repo`, `diff`, `files`; empty diff aborts.

## T-005 — `plan` node

- **Phase:** 2 · **Backlog:** Now (P0)
- Decide specialists from file types and diff size.
- Exit: returns an ordered node list; any planner error falls back to "run all".

## T-006 — Specialist nodes

- **Phase:** 2 · **Backlog:** Next (P1)
- `bug_hunter`, `security_auditor`, `style_linter`, `test_gap_analyzer`, `summarizer`.
- Exit: each returns `list[Finding]`; temperature `0` (`0.2` summarizer); retry ×2 then record
  into `ReviewState.errors`.

## T-007 — `aggregate` node

- **Phase:** 2 · **Backlog:** Next (P1)
- Merge, dedupe (file + line + category), sort by severity then confidence.
- Exit: never raises; stats per severity correct.

## T-008 — `report` node

- **Phase:** 2 · **Backlog:** Next (P1)
- Render markdown PR comment and `review_report.json` (`SPECIFICATION.md §6`).
- Exit: `trace_url` included when tracing is on; renderer failure aborts with `2`.

## T-009 — ChromaDB bootstrap + ingestion

- **Phase:** 3 · **Backlog:** Next (P1)
- Create `project_conventions`, `past_reviews`, `codebase_docs`; embed repo docs.
- Exit: `python -m app.ingest ./repo` populates all three collections.

## T-010 — `context_retriever` node

- **Phase:** 3 · **Backlog:** Next (P1)
- Query built from the diff; return ≤ 8 chunks.
- Exit: on retrieval error returns empty context and logs — never raises.

## T-011 — LangSmith tracing

- **Phase:** 4 · **Backlog:** Next (P1)
- One trace per run, one span per node, prompt versions tagged.
- Exit: report contains a working `trace_url` when `LANGSMITH_API_KEY` is set.

## T-012 — Docker image

- **Phase:** 5 · **Backlog:** Later (P2)
- Single image, entrypoints for CLI / CI worker / service.
- Exit: `docker run --env-file .env -v "$PWD:/repo" … review /repo/diff.patch` reproduces the
  local result.

## T-013 — CI worker

- **Phase:** 5 · **Backlog:** Later (P2)
- Invoke the container on `pull_request`; surface exit `1` as check failure, exit `2` as
  infrastructure failure.
- Exit: pipeline gates on the verdict without parsing markdown.

## T-014 — Webhook service

- **Phase:** 5 · **Backlog:** Later (P2)
- Long-running API receiving provider webhooks, posts the PR comment.
- Exit: comment appears on the PR; run traced end to end. See `OPERATIONS.md`.

## Task rules

- One task touches one node or one contract — no cross-cutting mega-tasks.
- A task may not start before its phase's sequencing rules allow it (`ROADMAP.md`).
- Done = tests green (`TESTING.md`) + docs updated (`CHANGELOG.md`, `FILES.md`).

## Related

- Priority order → `BACKLOGS.md`
- Phase gates → `ROADMAP.md`
- Contracts each task must satisfy → `SPECIFICATION.md`
