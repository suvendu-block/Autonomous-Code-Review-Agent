# TROUBLESHOOTING.md

Runbook when something goes wrong.

**Golden rule:** a run with no report and no error is a bug, not a mystery
(`PRINCIPLES.md §1`). Start from the trace.

## §1 — No output at all

1. Open the LangSmith project for the run (or check for a missing trace).
2. No trace → the run died before `start`; check process logs and exit code.
3. Trace exists → find the last completed span; the failing node is its child.
4. File an incident; do not re-run until the cause is known.

## §2 — Exit code 2 (run failed)

| Symptom | Likely cause | Fix |
|---|---|---|
| `LLM_API_KEY is required` | env not injected | check `.env` / pipeline secrets |
| provider 401/403 | key revoked or scoped wrong | rotate key |
| provider 429 | rate limit | reduce concurrency, add backoff (`BACKLOGS.md` P3) |
| `diff is empty` | bad diff generation in CI | fix the `git diff` step |
| ChromaDB open error | `CHROMA_PATH` missing or locked | mount volume, check permissions |
| OOM on large diff | diff over budget | confirm `MAX_DIFF_LINES` splitting |

## §3 — Exit code 1 but findings look wrong

1. Read the trace: which specialist produced it, with what context chunks?
2. Context suspicious → check ingestion (`project_conventions`, `codebase_docs` empty?).
3. Repeated finding already waived → `past_reviews` not populated or not queried
   (`BACKLOGS.md` P2).
4. Genuinely wrong → fix prompt + add an eval case (`TESTING.md §4`), don't tune per run.

## §4 — Exit code 0 but a real bug slipped through

1. Was the file even in the plan? Check the `plan` span.
2. Was the specialist skipped after retries? Errors are listed in the report.
3. Add the case to the eval dataset; a missing test is the fix, not a looser threshold.

## §5 — Tracing missing

- `LANGSMITH_API_KEY` unset → tracing off by default; set it. Prod requires it
  (`OPERATIONS.md`).
- Spans missing for a node → the node was added without instrumentation; that violates
  `PRINCIPLES.md §7`. Fix the node.

## §6 — Slow or expensive runs

| Check | Action |
|---|---|
| Diff size | confirm per-file splitting for diffs > `MAX_DIFF_LINES` |
| Plan node running all specialists | expected fallback; investigate planner inputs |
| Retrieval returning 8 chunks every time | normal ceiling; verify chunk relevance |
| Token spike | compare model id in report with `LLM_MODEL` |

## §7 — CI confusion

- Exit `1` and exit `2` must never be reported the same way (`DECISIONS.md ADR-008`).
  Exit `1` = code verdict; exit `2` = infrastructure failure, surface as a broken check, not
  a review verdict.

## Collecting evidence for a bug report

```
run id / trace URL
image tag + git SHA
exit code
differ (diff head, size)
config summary (no secrets): model, severity mode, MAX_DIFF_LINES
report or error entry verbatim
```

## Related

- Signals and escalation → `HUMAN.md`
- Alert table → `OPERATIONS.md`
