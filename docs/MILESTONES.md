# MILESTONES.md

Project vision and milestones.

## M0 — Skeleton (current)

- Repo, docs set, `index.py` entry point.
- Config and data contracts defined in `SPECIFICATION.md`.

## M1 — Single-pass reviewer

- Load a diff from CLI.
- One specialist (`bug_hunter`) runs against the diff.
- Emits `ReviewReport` as markdown + `review_report.json`.
- Exit codes `0 | 1 | 2` implemented.

## M2 — Supervisor graph

- LangGraph graph: `start → plan → specialists → aggregate → report`.
- All five specialists live: `bug_hunter`, `security_auditor`, `style_linter`,
  `test_gap_analyzer`, `summarizer`.
- `context_retriever` reads from ChromaDB.

## M3 — Memory & grounding

- Three collections populated: `project_conventions`, `past_reviews`, `codebase_docs`.
- Findings deduped against `past_reviews` so the agent stops repeating itself.

## M4 — Tracing & evaluation

- LangSmith traces one span per node.
- Eval dataset replayed on prompt changes; regressions block merge.

## M5 — Delivery

- Docker image; CLI, CI worker and webhook service shapes (`ARCHITECTURE.md`).
- Git provider integration posts the PR comment.

## M6 — Hardening

- Parallel branch review for large diffs.
- Cost/latency budgets, retry policy, troubleshooting runbook.

## Definition of done for any milestone

- Docs updated (`CHANGELOG.md`, `FILES.md`).
- Tests green (`TESTING.md`).
- No secrets in repo (`SECURITY.md`).
