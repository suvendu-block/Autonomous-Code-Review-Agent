# FILES.md

The file map. Every file listed here exists at the repo root or under `docs/`, and is
updated by the same change that invalidates it (`PRINCIPLES.md §11`).

## Current layout

```
Autonomous-Code-Review-Agent/
├── index.py                 # entry point: loads config, prints model + node list
├── requirements.txt         # pinned dependency ranges
├── .env.example             # config template (SECURITY.md)
├── .gitignore               # excludes .env, .venv/, .chroma/
├── app/
│   ├── __init__.py
│   ├── config.py            # env loader + validation (SPECIFICATION.md §2)
│   ├── models.py            # Finding, ReviewReport contracts (SPECIFICATION.md §3)
│   └── nodes.py             # NODE_ORDER registry (ARCHITECTURE.md)
├── tests/
│   ├── test_config.py       # config contract tests
│   ├── test_models.py       # data contract tests
│   └── test_index.py        # entry point + exit-code tests
└── docs/
    ├── ALL.md               # overview, docs map (start here)
    ├── PROJECT.md           # name, stack, goals, non-goals
    ├── VISION.md            # statement, future state, boundaries
    ├── MILESTONES.md        # M0–M6
    ├── ROADMAP.md           # phased plan + sequencing rules
    ├── BACKLOGS.md          # prioritised feature list
    ├── TASKS.md             # executable task breakdown
    ├── STEPS.md             # zero-to-production steps
    ├── ARCHITECTURE.md      # diagram, graph nodes, state
    ├── SPECIFICATION.md     # config, contracts, node specs, exit codes
    ├── REQUIREMENTS.md      # FR/NFR catalogue
    ├── PRINCIPLES.md        # design principles
    ├── DECISIONS.md         # ADR log
    ├── CONTRIBUTION.md      # workflow and conventions
    ├── HUMAN.md             # human-in-the-loop roles
    ├── CONVERSATION.md      # agent ↔ human message rules
    ├── TESTING.md           # test layers and gates
    ├── DEPLOYMENTS.md       # image, CI worker, service, environments
    ├── OPERATIONS.md        # running it: health, SLOs, alerts
    ├── TROUBLESHOOTING.md   # runbook
    ├── SECURITY.md          # secrets, access, injection
    ├── PRIVACY.md           # data map and third parties
    ├── FILES.md             # this file
    ├── CHANGELOG.md         # release history
    └── thoughts.md          # original idea notes
```

## Docs by category (as in `ALL.md`)

| Category | Files |
|---|---|
| Vision | `VISION.md`, `MILESTONES.md` |
| Planning | `ROADMAP.md`, `BACKLOGS.md`, `TASKS.md`, `STEPS.md` |
| Design | `ARCHITECTURE.md`, `SPECIFICATION.md`, `PRINCIPLES.md`, `DECISIONS.md` |
| Process | `CONTRIBUTION.md`, `HUMAN.md`, `CONVERSATION.md` |
| Operations | `DEPLOYMENTS.md`, `OPERATIONS.md`, `TESTING.md`, `TROUBLESHOOTING.md` |
| Policy | `SECURITY.md`, `PRIVACY.md` |
| Meta | `FILES.md`, `CHANGELOG.md` |
| Overview | `ALL.md`, `PROJECT.md`, `REQUIREMENTS.md`, `thoughts.md` |

## Planned code layout (not yet created)

| Path | Purpose | Roadmap phase |
|---|---|---|
| `app/cli.py` | `review <diff>` entrypoint | 1 |
| `app/graph/state.py` | `ReviewState` | 2 |
| `app/graph/nodes/` | `start`, `plan`, specialists, `aggregate`, `report` | 2 |
| `app/memory/chroma.py` | collections + ingestion | 3 |
| `app/tracing.py` | LangSmith spans | 4 |
| `Dockerfile` | delivery unit | 5 |
| `tests/unit`, `tests/graph`, `tests/contract` | see `TESTING.md` | 1–2 |
| `requirements.txt` | pinned dependencies | 1 |

## Rules

- Renaming a file updates `FILES.md`, `ALL.md` and every cross-reference in the same PR.
- A listed file that does not exist is a bug (exit criteria for `ROADMAP.md` 1.1).
- New files must be listed here before they merge.
