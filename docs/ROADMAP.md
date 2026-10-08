# ROADMAP.md

Development roadmap.

## Phase 1 — Foundations

| # | Item | Exit criteria |
|---|---|---|
| 1.1 | Project docs set | All files in `FILES.md` exist |
| 1.2 | Env config loader | All `SPECIFICATION.md §2` vars read + validated |
| 1.3 | `Finding` / `ReviewReport` models | Pydantic models importable, validated |
| 1.4 | CLI skeleton | `review <diff>` prints JSON, correct exit codes |

## Phase 2 — Graph

| # | Item | Exit criteria |
|---|---|---|
| 2.1 | `ReviewState` + `start` node | Diff loaded or abort on empty |
| 2.2 | `plan` node | Ordered node list, fallback = run all |
| 2.3 | Specialists | Each returns `list[Finding]`, retry ×2 |
| 2.4 | `aggregate` | Deduped, severity-sorted findings |
| 2.5 | `report` | Markdown + `review_report.json` |

## Phase 3 — Grounding

| # | Item | Exit criteria |
|---|---|---|
| 3.1 | ChromaDB bootstrap | Three collections created |
| 3.2 | Ingestion | Repo docs/conventions embedded |
| 3.3 | `context_retriever` | ≤ 8 chunks, empty on error |

## Phase 4 — Observability

| # | Item | Exit criteria |
|---|---|---|
| 4.1 | LangSmith tracing | One trace per run, span per node |
| 4.2 | Prompt versioning | Prompts tagged and traceable |
| 4.3 | Eval replay | Dataset run on prompt change |

## Phase 5 — Delivery

| # | Item | Exit criteria |
|---|---|---|
| 5.1 | Docker image | Reproducible local run |
| 5.2 | CI worker | Pipeline invokes container |
| 5.3 | Webhook service | Provider comment posted |
| 5.4 | Large-diff branching | Diffs > `MAX_DIFF_LINES` split per file |

## Sequencing rules

- Nothing in Phase 3 before Phase 2 contracts are stable.
- Nothing in Phase 5 before Phase 4 tracing exists (no unobservable deployments).
- Docs for a phase land with the phase, not after.

## Related

- Order of work → `STEPS.md`
- Fine-grained items → `TASKS.md`, `BACKLOGS.md`
- Dates/versions → `CHANGELOG.md`
