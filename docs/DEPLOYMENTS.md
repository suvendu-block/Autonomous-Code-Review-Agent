# DEPLOYMENTS.md

How the agent is packaged and shipped.

One image, three shapes (`DECISIONS.md ADR-005`).

## Build

```bash
docker build -t code-review-agent:latest .
docker run --rm code-review-agent --help
```

Image rules:

- Base image pinned by digest or minor version.
- No secrets in layers; `.env` is mounted or injected at runtime, never `COPY`ed.
- Non-root user; read-only root filesystem where possible.
- Layer order: deps → code → entrypoint, so code edits don't rebuild dependencies.

## Shape 1 — CLI (local)

```bash
docker run --rm --env-file .env -v "$PWD:/repo" \
  code-review-agent review /repo/diff.patch
```

Exit code is the verdict (`SPECIFICATION.md §7`).

## Shape 2 — CI worker

```yaml
# pull_request pipeline sketch
steps:
  - run: git diff origin/main...HEAD > /tmp/diff.patch
  - run: |
      docker run --rm --env-file .env -v "$PWD:/repo" \
        code-review-agent review /tmp/diff.patch
    env:
      # exit 1 = findings → fail the check
      # exit 2 = infrastructure → fail the check differently
```

- Post `review_report.json` as a pipeline artifact.
- Never treat exit `2` as a code verdict (`STEPS.md §7`).

## Shape 3 — Webhook service

- Long-running API; receives provider webhooks, runs the graph, posts the PR comment.
- Configuration and health checks → `OPERATIONS.md`.
- Requires tracing on, so every public run is auditable.

## Environments

| Env | Purpose | Tracing | Severity mode |
|---|---|---|---|
| local | Development, ad-hoc diffs | optional | `lenient` |
| ci | PR gating | on | `normal` |
| staging | Webhook rehearsal | on | `normal` |
| prod | Live PR reviews | on | `strict` |

## Promotion rules

1. Nothing reaches CI before Phase 4 tracing exists (`ROADMAP.md` sequencing rules).
2. Image tag = git SHA; `latest` moves only from a green pipeline.
3. Rollback = re-run previous tag; ChromaDB volume is state, back it up separately.
4. Config changes ship as env var changes, not image rebuilds (`DECISIONS.md ADR-006`).

## Stateful parts

| State | Location | Backup |
|---|---|---|
| ChromaDB collections | `CHROMA_PATH` volume | Snapshot with the pipeline |
| Traces | LangSmith project | Managed by provider |
| Reports | CI artifacts / PR comments | Durable in the provider |

## Related

- Runtime behaviour and on-call → `OPERATIONS.md`
- Release history → `CHANGELOG.md`
