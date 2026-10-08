# SPECIFICATION.md

Technical specification.

## 1. Runtime

- Python ≥ 3.11
- Package manager: `uv` or `pip` + `requirements.txt`
- LLM provider pluggable (OpenAI-compatible, Anthropic, or local) via env config.

## 2. Configuration

All config via environment variables (12-factor):

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_MODEL` | yes | — | Model id used by agents |
| `LLM_API_KEY` | yes | — | Provider key |
| `LANGSMITH_API_KEY` | no | — | Enables tracing |
| `LANGSMITH_PROJECT` | no | `code-review-agent` | Trace project name |
| `CHROMA_PATH` | no | `./.chroma` | Persist directory |
| `EMBEDDING_MODEL` | no | `text-embedding-3-small` | Embedding model |
| `MAX_DIFF_LINES` | no | `3000` | Truncation guard |
| `REVIEW_SEVERITY` | no | `normal` | `strict` \| `normal` \| `lenient` |

## 3. Data contracts

### Finding

```python
class Finding(BaseModel):
    file: str
    line: int | None
    severity: Literal["blocker", "major", "minor", "info"]
    category: Literal["bug", "security", "style", "testing", "docs", "performance"]
    title: str
    detail: str
    suggestion: str | None = None
    confidence: float = 0.5   # 0..1
```

### Review report

```python
class ReviewReport(BaseModel):
    summary: str
    findings: list[Finding]
    stats: dict[str, int]      # counts per severity
    model: str
    trace_url: str | None
```

## 4. Node specifications

| Node | Input | Output | Failure mode |
|---|---|---|---|
| `start` | diff source | `ReviewState` | abort if diff empty |
| `plan` | files + sizes | ordered node list | fallback = run all specialists |
| `context_retriever` | query from diff | ≤ 8 chunks | empty context on error (log) |
| specialists | diff + context | `list[Finding]` | retry ×2, then record error |
| `aggregate` | findings | deduped sorted findings | never fails |
| `report` | report | markdown / JSON | abort run |

## 5. Determinism & limits

- Temperature `0` for specialists, `0.2` for summarizer.
- Diff larger than `MAX_DIFF_LINES` is split per file and reviewed in parallel branches.
- Every run must produce either a report or an explicit error entry — never silence.

## 6. Output format

Markdown PR comment:

```markdown
## 🤖 Autonomous Review — <n> findings
| # | Severity | File | Issue |
|---|----------|------|-------|
...
### Details
1. **[blocker] security/api.py:42** — SQL string built from user input
   _Suggestion:_ use parameterized query.
```

Plus machine-readable `review_report.json` artifact.

## 7. Exit codes (CLI)

- `0` — review completed, no blocker/major findings
- `1` — review completed, blocker/major findings present
- `2` — review failed (config/runtime error)
