# ARCHITECTURE.md

Architecture of the project.

## High-level diagram

```
                 ┌──────────────────────────────┐
  Git provider ──▶  Webhook / CLI Trigger       │
                 └──────────────┬───────────────┘
                                ▼
                 ┌──────────────────────────────┐
                 │  Orchestrator (LangGraph)     │
                 │  supervisor → plan → route    │
                 └──────────────┬───────────────┘
        ┌───────────┬───────────┼───────────┬─────────────┐
        ▼           ▼           ▼           ▼             ▼
  ┌───────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐ ┌────────────┐
  │ context   │ │ bug     │ │security│ │ style /  │ │ test gap   │
  │ retriever │ │ hunter  │ │ auditor│ │ linter   │ │ analyzer   │
  └─────┬─────┘ └────┬────┘ └───┬────┘ └────┬─────┘ └─────┬──────┘
        │            │          │           │             │
        └────────────┴─────┬────┴───────────┴─────────────┘
                           ▼
                 ┌──────────────────────────────┐
                 │  Aggregator / Summarizer      │
                 │  severity merge + dedupe      │
                 └──────────────┬───────────────┘
                                ▼
                 ┌──────────────────────────────┐
                 │  Reporter (PR comment / JSON) │
                 └──────────────────────────────┘

  Cross-cutting: ChromaDB (memory) · LangSmith (traces) · Config (env)
```

## Graph nodes

| Node | Responsibility | Reads | Writes |
|---|---|---|---|
| `start` | Load diff + repo metadata | Git provider | `ReviewState` |
| `plan` | Decide which specialists to run | diff size, file types | `plan` |
| `context_retriever` | Fetch conventions / prior reviews | ChromaDB | `context` |
| `bug_hunter` | Logic errors, edge cases, race conditions | diff + context | `findings` |
| `security_auditor` | Injection, secrets, unsafe deserialization | diff + context | `findings` |
| `style_linter` | Naming, structure, project conventions | diff + context | `findings` |
| `test_gap_analyzer` | Untested paths, missing cases | diff + coverage | `findings` |
| `aggregate` | Merge, dedupe, rank by severity | all `findings` | `report` |
| `report` | Emit PR comment / JSON artifact | `report` | output |

## State

`ReviewState` is a TypedDict shared across nodes (LangGraph checkpointing friendly):

```python
class ReviewState(TypedDict):
    repo: str
    diff: str
    files: list[str]
    plan: list[str]
    context: str
    findings: list[Finding]
    report: str
    errors: list[str]
```

## Memory layer (ChromaDB)

- Collection `project_conventions` — extracted style/Architecture rules.
- Collection `past_reviews` — embeddings of previous findings to avoid repeats.
- Collection `codebase_docs` — README / docs snippets for domain context.

## Observability (LangSmith)

- One trace per review run; each graph node is a span.
- Prompt versions tracked; eval datasets replayed on prompt changes.

## Deployment shapes

1. **CLI** — local review of an uncommitted diff.
2. **CI worker** — Docker container invoked by pipeline.
3. **Service** — long-running API receiving webhooks (see `OPERATIONS.md`).

## Related

- `DECISIONS.md` records why LangGraph / ChromaDB / LangSmith were chosen.
- `SPECIFICATION.md` defines exact contracts for each node.
