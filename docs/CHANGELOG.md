# CHANGELOG.md

Release history. Format follows [Keep a Changelog](https://keepachangelog.com/);
versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added

- Config loader `app/config.py` with validation and fail-fast `ConfigError`
  (exit code `2`); `app/nodes.py` node registry; entry point prints model + node list
  (`STEPS.md §1`), covered by 15 tests.
- Data contracts `app/models.py` — `Finding` and `ReviewReport` pydantic models with
  severity/category literals and `confidence` bounds (`STEPS.md §2`), 17 contract tests.
- `requirements.txt`, `.env.example`, `.gitignore` (`STEPS.md §0`).
- Complete documentation set — all files listed in `FILES.md` / `ALL.md` docs map.
- Task breakdown `TASKS.md` (T-001 … T-014) mapped to `ROADMAP.md` phases.
- Process docs: `CONTRIBUTION.md`, `HUMAN.md`, `CONVERSATION.md`.
- Operations docs: `DEPLOYMENTS.md`, `OPERATIONS.md`, `TESTING.md`,
  `TROUBLESHOOTING.md`.
- Policy docs: `SECURITY.md`, `PRIVACY.md`.
- Meta docs: `FILES.md`, `CHANGELOG.md`.

## [0.1.0] — M0 Skeleton

### Added

- Repository skeleton with `index.py` entry point.
- Vision, milestones, roadmap, backlogs and principles.
- Architecture, specification and requirements: graph nodes, `ReviewState`, `Finding` /
  `ReviewReport` contracts, configuration table, exit codes `0 | 1 | 2`.
- ADR log (`DECISIONS.md`) — ADR-001 … ADR-008.

### Known gaps

- No graph, no memory, no tracing, no Docker image, no `review <diff>` CLI yet
  (`BACKLOGS.md` → Now).

## Versioning rules

- **Major** — a contract changes (`Finding`, `ReviewReport`, exit codes) or a documented
  deployment shape is removed.
- **Minor** — a node, specialist, backlog capability or doc section is added.
- **Patch** — prompt tuning, docs fixes, bug fixes with no contract change.
- Every release updates `FILES.md` if files moved, and `MILESTONES.md` if a milestone
  closed.
