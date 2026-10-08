# OPERATIONS.md

Running the agent in production.

## Service contract

- Entrypoint: container from `DEPLOYMENTS.md` shape 3.
- Endpoint: `POST /review` (webhook) and `GET /healthz`.
- Every request produces a report or an explicit error — never silence
  (`PRINCIPLES.md §1`).

## Configuration

All from environment (`SPECIFICATION.md §2`). Required in prod:

```
LLM_MODEL=...
LLM_API_KEY=...
LANGSMITH_API_KEY=...        # required in prod: no untraced runs
LANGSMITH_PROJECT=code-review-agent
CHROMA_PATH=/data/chroma
MAX_DIFF_LINES=3000
REVIEW_SEVERITY=strict
```

## Health

| Check | Signal | Meaning |
|---|---|---|
| liveness | `GET /healthz` → `200` | process up |
| readiness | `GET /healthz` → `200` only when ChromaDB reachable and config valid | safe to receive webhooks |
| run health | exit code per run | `0`/`1` verdict, `2` failure |

## SLOs

- Review completes in minutes, not hours (`REQUIREMENTS.md` NFR-1).
- p95 run duration budget by diff size; alert when exceeded.
- Error budget: any run without a report counts against it.

## Scaling

- Stateless workers; concurrency limited by provider rate limits, not by the graph.
- One ChromaDB volume, mounted read-mostly; ingestion is a separate batch job
  (`python -m app.ingest`).
- Large diffs split per file and reviewed in parallel branches
  (`REQUIREMENTS.md` FR-1.4) — each branch is a child span of one trace.

## Routine operations

| Task | Frequency | How |
|---|---|---|
| Re-ingest repo docs | on convention change | `python -m app.ingest ./repo` |
| Rotate `LLM_API_KEY` | per policy | update env, restart |
| Prune old traces | per retention policy | LangSmith project settings |
| Review cost per run | weekly | LangSmith run metadata |
| Verify exit codes | per release | `TESTING.md` contract tests |

## Alerts

| Alert | Condition | First action |
|---|---|---|
| Run produced no output | report missing and no error entry | `TROUBLESHOOTING.md` §1 — incident |
| Exit `2` rate above threshold | infra failures spiking | `TROUBLESHOOTING.md` §2 |
| Trace missing | run completed without `trace_url` | check `LANGSMITH_API_KEY` |
| Retriever returning 0 chunks | context empty across runs | check `CHROMA_PATH` volume |
| Cost/latency spike | per-run tokens or duration | check diff size, plan node |

## Deploy and rollback

- Deploy = new image tag from a green pipeline (`DEPLOYMENTS.md`).
- Rollback = previous tag; no schema migrations exist for ChromaDB beyond re-ingestion.
- Config-only changes: update env, restart, verify with one traced run.

## On-call handoff

Carry: current image tag, last green trace URL, open alerts, and the
`TROUBLESHOOTING.md` runbook. If a run is unexplained, it is a bug, not a mystery
(`PRINCIPLES.md §1`).
