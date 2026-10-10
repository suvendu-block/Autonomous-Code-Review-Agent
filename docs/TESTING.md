# TESTING.md

What we test and how.

## Layers

| Layer | Tool | Scope |
|---|---|---|
| Unit | `pytest` | contracts, pure functions, node logic |
| Graph | `pytest` | node wiring, state transitions, failure paths |
| Contract | `pytest` | exit codes, report schema, output format |
| Eval | LangSmith datasets | prompt/model regression |
| Smoke | Docker run | image boots, CLI behaves |

## Commands

```bash
python -m pytest                 # all tests
python -m pytest tests/unit      # pure functions (diff, parsing, render, memory)
python -m pytest tests/graph     # graph wiring + failure paths
python -m pytest tests/contract  # contracts, exit codes, CLI
python index.py                  # smoke: config + node list
```

## 1. Contract tests (non-negotiable)

- `Finding` accepts only `blocker | major | minor | info` severities and the six categories.
- `confidence` outside `0..1` is rejected.
- `ReviewReport` serializes to `review_report.json` and round-trips.
- Exit codes: clean → `0`, blocker/major present → `1`, runtime error → `2`
  (`SPECIFICATION.md §7`).

## 2. Graph tests

| Case | Expected |
|---|---|
| Empty diff | abort at `start`, explicit error, exit `2` |
| Planner throws | fallback = run all specialists |
| Specialist throws twice | error recorded in `ReviewState.errors`, run continues |
| Retriever throws | empty context, logged, run continues |
| `aggregate` with mixed severities | deduped, sorted, never raises |
| Report renderer throws | run aborts, exit `2` |

## 3. Determinism tests

- Same diff + same stubbed context → identical findings across two runs.
- Specialists run at temperature `0`, summarizer at `0.2`.

## 4. Eval (LangSmith)

- A dataset of real diffs with labelled expected findings.
- Replay on every prompt or model change; a regression blocks merge
  (`MILESTONES.md` M4).
- Metrics: recall on blockers/majors, false-positive rate on `info`.

## 5. Smoke tests

```bash
docker build -t code-review-agent .
docker run --rm --env-file .env -v "$PWD:/repo" \
  code-review-agent review /repo/fixtures/clean.patch    # expect 0
  # fixtures/blocker.patch → expect 1
  # missing config          → expect 2
```

## Coverage expectations

- Node failure modes (`SPECIFICATION.md §4`) each have a test.
- Untested node = not shippable; coverage gaps are backlog items for
  `test_gap_analyzer` fixtures.

## Gate

A change is mergeable when: unit + graph + contract tests green, smoke exit codes correct,
and eval replay shows no regression (`CONTRIBUTION.md`).
