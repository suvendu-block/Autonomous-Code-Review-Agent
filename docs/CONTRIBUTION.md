# CONTRIBUTION.md

How to contribute.

## Ground rules

1. Read `PRINCIPLES.md` first — it defines what we refuse to build.
2. Small, reviewable changes. One task (`TASKS.md`) per PR where possible.
3. No secrets, ever (`SECURITY.md`).
4. Every change that invalidates a doc updates that doc in the same PR.

## Workflow

1. Branch from the current trunk: `feat/T-003-cli-skeleton`, `fix/report-exit-code`.
2. Implement the task and its tests (`TESTING.md`).
3. Run the local gate:

```bash
python -m pytest
python index.py
```

4. Update docs if behaviour changed (`FILES.md` lists what must stay truthful).
5. Open a PR; a human approves — the review agent may comment, never merge
   (`PRINCIPLES.md §3`).

## Commit style

- Imperative subject: `add plan node fallback`
- Reference the task id: `T-005: plan node fallback to run-all`
- Keep the body to *why*, not *what*.

## Code conventions

- Python ≥ 3.11, type hints on public functions.
- Node boundaries carry only `Finding` / `ReviewReport` (`PRINCIPLES.md §5`).
- Every new node ships with its LangSmith span and a documented failure mode
  (`SPECIFICATION.md §4`).
- Config comes from environment variables only — no config files
  (`DECISIONS.md ADR-006`).

## Adding a specialist agent

1. Add the node to the graph and to the tables in `ARCHITECTURE.md` and
   `SPECIFICATION.md §4`.
2. Define its failure mode (retry count, fallback output).
3. Add a prompt with a version tag and an eval case (`TESTING.md`).
4. Add a backlog entry and, if it changes the plan logic, update `plan` in `TASKS.md`.

## Review expectations

- Findings from the agent are advisory; a human decides.
- Blocker/major findings from CI (exit `1`) must be addressed or explicitly waived in the PR.
- Exit `2` is an infrastructure failure — fix the run, don't argue about the verdict.

## Docs discipline

- A file listed in `FILES.md` that no longer exists is a bug.
- New decisions go to `DECISIONS.md` as ADR-NNN, not to chat history.
