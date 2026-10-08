# STEPS.md

Steps — From Zero to Production.

## 0. Environment

```bash
# Python >= 3.11, uv or pip
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

Create `.env` (never commit it — see `SECURITY.md`):

```
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=...
LANGSMITH_API_KEY=...        # optional, enables tracing
LANGSMITH_PROJECT=code-review-agent
CHROMA_PATH=./.chroma
EMBEDDING_MODEL=text-embedding-3-small
MAX_DIFF_LINES=3000
REVIEW_SEVERITY=normal
```

## 1. Verify the skeleton

```bash
python index.py            # loads config, prints model + node list
python -m pytest           # see TESTING.md
```

## 2. Data contracts

1. Add `Finding` and `ReviewReport` models from `SPECIFICATION.md §3`.
2. Unit-test validation: severity/category literals, confidence bounds.

## 3. Graph

1. Define `ReviewState` (`ARCHITECTURE.md`).
2. Nodes in order: `start → plan → context_retriever → specialists → aggregate → report`.
3. `plan` fallback = run all specialists.
4. Specialists: temperature `0`, retry ×2, then record error.
5. `aggregate` never fails.

## 4. Memory

```bash
python -m app.ingest ./repo     # creates project_conventions, past_reviews, codebase_docs
```

## 5. Tracing

Set `LANGSMITH_API_KEY`, run one review, open the trace URL from the report.

## 6. Package

```bash
docker build -t code-review-agent .
docker run --rm --env-file .env -v "$PWD:/repo" code-review-agent review /repo/diff.patch
```

## 7. Wire into CI

Invoke the container on `pull_request`. Treat exit code `1` as "review found blocker/major",
exit code `2` as infrastructure failure → surface as a check failure, not a code verdict.

## 8. Service shape (optional)

Long-running API receiving webhooks — see `OPERATIONS.md`, `DEPLOYMENTS.md`.

## 9. Go-live checklist

- [ ] No secrets in repo (`SECURITY.md`)
- [ ] Exit codes match spec
- [ ] Every run produces a report or explicit error
- [ ] LangSmith project receiving traces
- [ ] `TROUBLESHOOTING.md` reviewed on-call
