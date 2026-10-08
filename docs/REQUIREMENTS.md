# REQUIREMENTS.md

Functional requirements.

## FR-1 — Input

| ID | Requirement |
|---|---|
| FR-1.1 | Accept a diff from a file path or stdin via CLI |
| FR-1.2 | Accept a repository path for context retrieval |
| FR-1.3 | Abort with an explicit error if the diff is empty |
| FR-1.4 | Split diffs larger than `MAX_DIFF_LINES` per file and review them in parallel branches |

## FR-2 — Review

| ID | Requirement |
|---|---|
| FR-2.1 | Plan which specialists run (`plan`), with fallback = run all |
| FR-2.2 | Retrieve ≤ 8 context chunks from ChromaDB; empty context on retrieval error (logged) |
| FR-2.3 | Run `bug_hunter`, `security_auditor`, `style_linter`, `test_gap_analyzer`, `summarizer` |
| FR-2.4 | Each finding conforms to the `Finding` contract (file, severity, category, confidence) |
| FR-2.5 | Retry a failed specialist ×2, then record the error in `ReviewState.errors` |
| FR-2.6 | Deduplicate and rank findings by severity in `aggregate` |

## FR-3 — Output

| ID | Requirement |
|---|---|
| FR-3.1 | Emit a markdown PR comment with a findings table and details section |
| FR-3.2 | Emit machine-readable `review_report.json` |
| FR-3.3 | Report includes summary, stats per severity, model id, trace URL when tracing is on |
| FR-3.4 | Every run produces a report or an explicit error entry — never silence |

## FR-4 — CLI contract

| ID | Requirement |
|---|---|
| FR-4.1 | Exit `0` — completed, no blocker/major findings |
| FR-4.2 | Exit `1` — completed, blocker/major findings present |
| FR-4.3 | Exit `2` — review failed (config/runtime error) |

## FR-5 — Memory

| ID | Requirement |
|---|---|
| FR-5.1 | Maintain collections `project_conventions`, `past_reviews`, `codebase_docs` |
| FR-5.2 | Learn conventions by retrieval rather than hard-coded rules |

## FR-6 — Tracing

| ID | Requirement |
|---|---|
| FR-6.1 | One LangSmith trace per run, one span per node, when `LANGSMITH_API_KEY` is set |
| FR-6.2 | Include `trace_url` in the report when available |

## Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | Review completes in minutes, not hours |
| NFR-2 | Specialist temperature `0`; summarizer `0.2` |
| NFR-3 | Configurable severity mode `strict \| normal \| lenient` |
| NFR-4 | No secrets in code, images or traces (`SECURITY.md`) |
| NFR-5 | Identical behaviour local / CI / service via one Docker image |

## Out of scope

- Auto-merge without human approval.
- Design-level review replacement.
- Non-Python languages on day one.
