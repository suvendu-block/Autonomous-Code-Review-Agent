# PRINCIPLES.md

Design principles.

## 1. Report or fail — never silence

Every run ends in a markdown/JSON report **or** an explicit error entry. A silent run is a
bug.

## 2. Retrieval over hard-coded rules

Project conventions come from the repository via ChromaDB, not from a rules file that rots.

## 3. Human decides

The agent proposes findings; a human approves the merge. No auto-merge, ever.

## 4. Deterministic where it matters

Temperature `0` for specialists, `0.2` for summarizer. Same diff + same context → same
findings, so regressions are measurable.

## 5. Contracts before code

`Finding` and `ReviewReport` are the only shapes that cross a node boundary. Nodes may not
invent ad-hoc structures.

## 6. Every node has a failure mode

Defined in `SPECIFICATION.md §4`. Empty context on error, retry ×2 on specialists,
`aggregate` never fails, `report` aborts the run.

## 7. Observability is not optional

No node ships without a LangSmith span. If it isn't traced, it didn't happen.

## 8. Bounded work

`MAX_DIFF_LINES` truncation, ≤ 8 context chunks, per-file splitting for large diffs. The
agent has a budget and respects it.

## 9. Evidence in every finding

A finding without `file`, `line` (where known) and `detail` is not a finding — it's an
opinion. Confidence is explicit.

## 10. Boring, reproducible delivery

One Docker image, env-var config, no hidden state outside `CHROMA_PATH`.

## 11. Docs live next to code

Every file listed in `FILES.md` exists at the repo root and is updated with the change that
invalidates it.
