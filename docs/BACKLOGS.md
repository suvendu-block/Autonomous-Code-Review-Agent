# BACKLOGS.md

Every feature.

## Now (P0)

- [x] Env config loader with validation and fail-fast errors
- [x] `Finding` / `ReviewReport` pydantic models
- [ ] CLI: read diff from file/stdin, emit report, exit codes 0/1/2
- [ ] LangGraph graph wiring `start → plan → specialists → aggregate → report`
- [ ] `ReviewState` TypedDict shared across nodes

## Next (P1)

- [ ] `context_retriever` with ChromaDB (≤ 8 chunks)
- [ ] ChromaDB ingestion pipeline for repo docs and conventions
- [ ] All five specialists with per-node prompts
- [ ] Severity dedupe/rank in `aggregate`
- [ ] Markdown PR comment template + `review_report.json` artifact
- [ ] LangSmith tracing (span per node)

## Later (P2)

- [ ] `past_reviews` dedupe so repeat findings are suppressed
- [ ] Parallel per-file branches for diffs > `MAX_DIFF_LINES`
- [ ] Severity mode `strict | normal | lenient` behaviour
- [ ] Git provider webhook service + PR comment posting
- [ ] Docker Compose dev environment
- [ ] Eval dataset + prompt regression gate

## Nice to have (P3)

- [ ] Multi-language support beyond Python
- [ ] Coverage input for `test_gap_analyzer`
- [ ] Cost/latency dashboard per run
- [ ] Auto-suggested patch files (diff format) per finding
- [ ] Retry with backoff on provider rate limits

## Ideas inbox

- [ ] Learn from human review comments on merged PRs
- [ ] Custom specialist plugins loaded from repo config
- [ ] Baseline mode: only report on lines changed in the diff

## Prioritisation

Priority = user impact × blocked-dependents ÷ effort. See `TASKS.md` for the executable
breakdown and `PRINCIPLES.md` for what we refuse to build.
