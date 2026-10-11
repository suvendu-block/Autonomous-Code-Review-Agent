# FILES.md

The file map. Every file listed here exists at the repo root or under `docs/`, and is
updated by the same change that invalidates it (`PRINCIPLES.md §11`).

## Current layout

```
Autonomous-Code-Review-Agent/
├── README.md                # project overview, quick start, usage
├── index.py                 # CLI: config skeleton + review <diff> (exit 0/1/2)
├── conftest.py              # root pytest conftest (sys.path)
├── requirements.txt         # pinned dependency ranges
├── Dockerfile               # delivery unit (DEPLOYMENTS.md)
├── .dockerignore            # keeps secrets/tests/docs out of layers
├── .env.example             # config template (SECURITY.md)
├── .gitignore               # excludes .env, .venv/, .chroma/
├── .github/
│   └── workflows/
│       ├── ci.yml           # pytest + image build/smoke
│       └── review.yml       # PR review worker (STEPS.md §7)
├── app/
│   ├── __init__.py
│   ├── config.py            # env loader + validation (SPECIFICATION.md §2)
│   ├── models.py            # Finding, ReviewReport contracts (SPECIFICATION.md §3)
│   ├── state.py             # ReviewState TypedDict (ARCHITECTURE.md)
│   ├── nodes.py             # NODE_ORDER + node impls + build_graph
│   ├── llm.py               # OpenAI-compatible client, temperature 0
│   ├── prompts.py           # specialist + summarizer prompts
│   ├── parsing.py           # untrusted LLM text → Finding coercion
│   ├── diff.py              # parse/split diffs (MAX_DIFF_LINES guard)
│   ├── render.py            # markdown PR comment (SPECIFICATION.md §6)
│   ├── tracing.py           # LangSmith trace + per-node spans
│   ├── memory.py            # ChromaDB collections, ingest, retrieval
│   ├── runner.py            # run_review: chunks → graph → exit code
│   └── ingest.py            # python -m app.ingest (STEPS.md §4)
├── fixtures/
│   ├── clean.patch          # smoke: expect exit 0
│   └── blocker.patch        # smoke: expect exit 1
├── tests/
│   ├── conftest.py          # shared fixtures (settings, FakeLLM, diffs)
│   ├── contract/            # config, models, exit codes, CLI
│   ├── graph/               # node wiring + failure paths
│   └── unit/                # diff, parsing, render, memory, tracing, llm
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

## Not yet created

| Path | Purpose | Roadmap phase |
|---|---|---|
| `app/service.py` | webhook service entrypoint (T-014) | 5 |

## Rules

- Renaming a file updates `FILES.md`, `ALL.md` and every cross-reference in the same PR.
- A listed file that does not exist is a bug (exit criteria for `ROADMAP.md` 1.1).
- New files must be listed here before they merge.
