# Autonomous Code Review Agent

An autonomous, multi-agent code review system that reads a pull request / diff, retrieves relevant project context from a vector store, runs specialized review agents over the change, and posts a structured, actionable review comment.

Built with **Python 3.11+**, **LangGraph**, **ChromaDB**, **LangSmith**, and **Docker**.

```
diff ─▶ start ─▶ plan ─▶ context_retriever ─▶ bug_hunter ─▶ security_auditor
                   ─▶ style_linter ─▶ test_gap_analyzer ─▶ aggregate ─▶ report ─▶ markdown + JSON
```

## Features

- **Multi-agent pipeline** — four specialist reviewers (`bug_hunter`, `security_auditor`, `style_linter`, `test_gap_analyzer`) orchestrated by a LangGraph state machine, each with its own prompt at temperature 0.
- **Smart planning** — the `plan` node selects which specialists run based on the changed file types; falls back to running all of them.
- **Vector memory** — ChromaDB collections (`project_conventions`, `past_reviews`, `codebase_docs`) provide retrieved context (≤ 8 chunks) and record past findings for future runs.
- **Tracing** — one LangSmith trace per run with a span per node; the trace URL is embedded in the report (optional).
- **Large-diff handling** — diffs over `MAX_DIFF_LINES` are split per file; oversized files are truncated with an explicit marker.
- **Deterministic failure modes** — specialists retry ×2 then record errors; every run produces a report or an explicit error. Never silence.
- **CI contract via exit codes** — `0` clean · `1` blocker/major findings · `2` failure (config/runtime/infra).
- **Severity modes** — `strict`, `normal` (default), `lenient` (drops `info` findings).
- **GitHub Actions worker** — comments the review on pull requests automatically.
- **Containerized** — non-root `python:3.11-slim` image, `.env` never baked into layers.

## Quick start

Requires Python ≥ 3.11.

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt
# or with uv: uv venv && uv pip install -r requirements.txt

# 2. Configure
cp .env.example .env        # then set LLM_API_KEY (and LLM_MODEL if needed)

# 3. Smoke test
python index.py             # prints model + node list
python -m pytest            # run the test suite

# 4. Review a diff
python index.py review fixtures/clean.patch     # exit 0
python index.py review fixtures/blocker.patch   # exit 1 (SQL injection + eval)
git diff main...HEAD | python index.py review - # read from stdin
```

The markdown report goes to **stdout**; node errors go to **stderr**; a machine-readable artifact is written to `review_report.json`.

## CLI

```
usage: index.py [review <diff|->]

commands:
  (none)             load config, print model + node list
  review <diff|->    run an autonomous review over a unified diff
                     ('-' reads from stdin; -o sets the JSON
                     artifact path, default review_report.json)
  --help             show this message

exit codes: 0 clean · 1 blocker/major findings · 2 failure
```

`review` options:

| Flag | Description |
|---|---|
| `diff` | path to a unified diff, or `-` for stdin |
| `-o, --output` | JSON artifact path (default `review_report.json`) |
| `--repo` | repository label recorded with findings |
| `--no-record` | skip writing findings into the `past_reviews` collection |

Examples:

```bash
python index.py review pr.diff --repo org/repo --no-record
python index.py review fixtures/blocker.patch -o report.json
```

### Ingest project context (optional)

Embed your repo's docs and conventions into ChromaDB so the `context_retriever` node has something to retrieve:

```bash
python -m app.ingest ./repo            # create/update collections
python -m app.ingest ./repo --reset    # drop collections first
```

If `CHROMA_PATH` doesn't exist, retrieval is simply disabled — the review still runs.

## Configuration

Environment variables only (loaded from `.env` via pydantic-settings). See `.env.example`.

| Variable | Required | Default | Notes |
|---|---|---|---|
| `LLM_MODEL` | yes | — | model id, e.g. `gpt-4o-mini` |
| `LLM_API_KEY` | yes | — | provider API key |
| `OPENAI_BASE_URL` | no | — | route to any OpenAI-compatible provider |
| `LANGSMITH_API_KEY` | no | — | empty ⇒ tracing off |
| `LANGSMITH_PROJECT` | no | `code-review-agent` | |
| `CHROMA_PATH` | no | `./.chroma` | missing path ⇒ retriever disabled |
| `EMBEDDING_MODEL` | no | `text-embedding-3-small` | |
| `MAX_DIFF_LINES` | no | `3000` | must be > 0; split/truncation guard |
| `REVIEW_SEVERITY` | no | `normal` | `strict` \| `normal` \| `lenient` |

Validation failures print `config error: …` and exit **2**.

## Architecture

| Module | Responsibility |
|---|---|
| `index.py` | CLI entry point (`review` command, exit codes) |
| `app/runner.py` | `run_review` orchestration: chunking → graph → exit code |
| `app/nodes.py` | `NODE_ORDER`, node implementations, `build_graph` |
| `app/config.py` | env loading + validation (`ConfigError`) |
| `app/models.py` | `Finding` / `ReviewReport` pydantic contracts |
| `app/state.py` | `ReviewState` TypedDict shared across nodes |
| `app/llm.py` | OpenAI-compatible chat client |
| `app/prompts.py` | specialist + summarizer prompts |
| `app/parsing.py` | untrusted LLM text → `Finding` coercion |
| `app/diff.py` | diff parsing, splitting, `MAX_DIFF_LINES` guard |
| `app/render.py` | markdown PR-comment renderer |
| `app/memory.py` | ChromaDB collections, ingest, retrieval, record |
| `app/ingest.py` | `python -m app.ingest` ingestion CLI |
| `app/tracing.py` | LangSmith trace + per-node spans |

Pipeline nodes: `start → plan → context_retriever → bug_hunter → security_auditor → style_linter → test_gap_analyzer → aggregate → report`.

Full details in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/SPECIFICATION.md`](docs/SPECIFICATION.md).

## Docker

```bash
docker build -t code-review-agent:latest .

# review a diff mounted from the host
docker run --rm --env-file .env -v "$PWD:/repo" \
  code-review-agent review /repo/fixtures/clean.patch

docker run --rm code-review-agent --help
```

The image runs as a non-root user and never copies `.env`.

## GitHub Actions

Two workflows in `.github/workflows/`:

- **`ci.yml`** — runs the pytest suite plus Docker build/smoke tests on pushes to `main` and on PRs.
- **`review.yml`** — PR review worker: builds the image, diffs against the merge base, runs the agent, uploads `review_report.json` + `review.md` artifacts, and comments the review on the PR when exit code = 1.

Required repository secrets: `LLM_API_KEY` (the workflow skips gracefully if unset), optionally `LLM_MODEL` and `LANGSMITH_API_KEY`.

## Testing

```bash
python -m pytest                  # everything
python -m pytest tests/unit       # diff, parsing, render, memory, tracing, llm
python -m pytest tests/graph      # node wiring + failure paths
python -m pytest tests/contract   # config, models, exit codes, CLI
python index.py                   # skeleton smoke
```

Docker smoke: `fixtures/clean.patch` → exit 0, `fixtures/blocker.patch` → exit 1, missing config → exit 2.

## Project layout

```
Autonomous-Code-Review-Agent/
├── index.py            # CLI entry point
├── app/                # pipeline, config, contracts, memory, tracing
├── fixtures/           # clean.patch (exit 0), blocker.patch (exit 1)
├── tests/              # contract / graph / unit suites
├── docs/               # full documentation set (start with docs/ALL.md)
├── .github/workflows/  # ci.yml + review.yml
├── Dockerfile
└── requirements.txt
```

## Documentation

The full doc set lives in [`docs/`](docs/) — start with [`docs/ALL.md`](docs/ALL.md), then `VISION.md` and `ARCHITECTURE.md`. Key pages:

| Topic | File |
|---|---|
| Overview & doc map | `docs/ALL.md` |
| Project summary & goals | `docs/PROJECT.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| Config, contracts, exit codes | `docs/SPECIFICATION.md` |
| Testing layers & gates | `docs/TESTING.md` |
| Deployment shapes | `docs/DEPLOYMENTS.md` |
| Contributing workflow | `docs/CONTRIBUTION.md` |
| Security & secrets | `docs/SECURITY.md` |

## Status

**Built:** config + contracts, LangGraph review pipeline, ChromaDB memory, LangSmith tracing, `review <diff>` CLI, Docker image, CI + PR-review workflows.

**Not started:** webhook service (`app/service.py`, task T-014) — see `docs/ROADMAP.md`.
