"""Review orchestration: chunks → graph → verdict.

Implements ``SPECIFICATION.md §5`` (large diffs split per file) and
§7 (exit codes). ``run_review`` never returns silently: either a result
with a rendered report, or a :class:`ReviewError` (caller exits ``2``).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from app.config import Settings
from app.diff import split_diff
from app.llm import LLM, build_llm
from app.memory import record_review
from app.nodes import SPECIALISTS, GraphContext, build_graph
from app.state import ReviewState, initial_state
from app.tracing import Tracer


class ReviewError(RuntimeError):
    """Fatal review failure — caller reports it and exits with code 2."""


@dataclass
class ReviewResult:
    state: ReviewState
    markdown: str
    exit_code: int
    trace_url: str | None = None


def compute_exit_code(state: ReviewState) -> int:
    """SPECIFICATION.md §7 — 0 clean, 1 blocker/major, 2 review failed."""
    plan = state.get("plan") or []
    planned = [name for name in plan if name in SPECIALISTS]
    errors = state.get("errors") or []
    findings = state.get("findings") or []

    if planned:
        failed = [
            name for name in planned
            if any(error.startswith(name + ":") for error in errors)
        ]
        if len(failed) == len(planned):
            return 2  # every specialist failed — no review actually happened

    if any(f.severity in ("blocker", "major") for f in findings):
        return 1
    return 0


def run_review(
    diff: str,
    settings: Settings,
    *,
    llm: LLM | None = None,
    tracer: Tracer | None = None,
    retriever=None,
    output_path: str | None = "review_report.json",
    record: bool = False,
    repo: str = "",
) -> ReviewResult:
    """Run the full review graph over ``diff`` and return the verdict."""
    llm = llm or build_llm(settings)
    tracer = tracer or Tracer(
        settings.langsmith_api_key, settings.langsmith_project
    )
    ctx = GraphContext(
        settings=settings,
        llm=llm,
        tracer=tracer,
        retriever=retriever,
        output_path=output_path,
    )
    graph = build_graph(ctx)
    chunks = split_diff(diff, settings.max_diff_lines)

    tracer.start_trace(
        {
            "model": settings.llm_model,
            "repo": repo,
            "diff_lines": len(diff.splitlines()),
            "chunks": len(chunks),
            "severity": settings.review_severity,
        }
    )

    state = initial_state(repo=repo)
    try:
        for index, chunk in enumerate(chunks):
            last = index == len(chunks) - 1
            # Only the final chunk emits the artifact / records the review.
            ctx.output_path = output_path if last else None
            ctx.record_review = (
                (lambda report: record_review(settings, report))
                if (record and last)
                else None
            )
            state = graph.invoke({**state, "diff": chunk})
    except Exception as exc:
        message = str(exc).strip() or exc.__class__.__name__
        tracer.finish_trace({"error": message})
        raise ReviewError(message) from exc

    exit_code = compute_exit_code(state)
    tracer.finish_trace(
        {
            "findings": len(state.get("findings", [])),
            "errors": state.get("errors", []),
            "exit_code": exit_code,
        }
    )

    markdown = state.get("report", "")
    trace_url = tracer.trace_url
    if trace_url and trace_url not in markdown:
        markdown = markdown + f"\n\n_Trace: {trace_url}_"
    return ReviewResult(
        state=state,
        markdown=markdown,
        exit_code=exit_code,
        trace_url=trace_url,
    )


def _log(message: str) -> None:
    print(message, file=sys.stderr)
