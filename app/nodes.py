"""Graph node registry and implementations (ARCHITECTURE.md — Graph nodes).

Linear pipeline: ``start → plan → context_retriever → specialists →
aggregate → report``. ``plan`` decides which specialists actually run; the
others skip via a guard, keeping execution order identical to
``NODE_ORDER`` while honouring ``SPECIFICATION.md §4`` failure modes.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from app import prompts
from app.config import Settings
from app.diff import parse_changed_files, retriever_query
from app.llm import LLM
from app.memory import MAX_CONTEXT_CHUNKS
from app.models import Finding, ReviewReport
from app.parsing import parse_findings
from app.render import render_markdown
from app.state import ReviewState
from app.tracing import Tracer

NODE_ORDER: list[str] = [
    "start",
    "plan",
    "context_retriever",
    "bug_hunter",
    "security_auditor",
    "style_linter",
    "test_gap_analyzer",
    "aggregate",
    "report",
]

SPECIALISTS: tuple[str, ...] = (
    "bug_hunter",
    "security_auditor",
    "style_linter",
    "test_gap_analyzer",
)

SEVERITIES: tuple[str, ...] = ("blocker", "major", "minor", "info")
SEVERITY_RANK: dict[str, int] = {name: i for i, name in enumerate(SEVERITIES)}

RETRY_ATTEMPTS = 3  # initial attempt + retry ×2 (SPECIFICATION.md §4)
SUMMARY_TEMPERATURE = 0.2
SPECIALIST_TEMPERATURE = 0.0

CODE_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt",
    ".c", ".h", ".cpp", ".hpp", ".rb", ".php", ".cs", ".sh", ".sql",
}


class StartError(RuntimeError):
    """Fatal failure at the ``start`` node (abort, exit 2)."""


class ReportError(RuntimeError):
    """Fatal failure at the ``report`` node (abort, exit 2)."""


@dataclass
class GraphContext:
    """Dependencies injected into every node (built by ``app.runner``)."""

    settings: Settings
    llm: LLM
    tracer: Tracer
    retriever: Callable[[str], list[str]] | None = None
    output_path: str | None = None
    record_review: Callable[[ReviewReport], Any] | None = None


def decide_specialists(files: list[str], diff: str) -> list[str]:
    """Choose specialists from file types (``plan`` fallback = run all)."""
    has_code = any(Path(f).suffix.lower() in CODE_SUFFIXES for f in files)
    chosen = {"bug_hunter", "security_auditor"}
    if has_code:
        chosen |= {"style_linter", "test_gap_analyzer"}
    elif files:
        chosen.add("style_linter")
    else:
        return list(SPECIALISTS)  # unknown scope — run everything
    return [name for name in SPECIALISTS if name in chosen]


def _log(message: str) -> None:
    print(message, file=sys.stderr)


def _start(state: ReviewState, ctx: GraphContext) -> dict:
    diff = state.get("diff") or ""
    if not diff.strip():
        raise StartError("diff is empty — aborting review (SPECIFICATION §4)")
    return {"files": parse_changed_files(diff)}


def _plan(state: ReviewState, ctx: GraphContext) -> dict:
    try:
        plan = decide_specialists(state.get("files", []), state.get("diff", ""))
        if not plan:
            plan = list(SPECIALISTS)
    except Exception as exc:  # planner failure → fallback = run all
        _log(f"plan fallback (run all specialists): {exc}")
        plan = list(SPECIALISTS)
    return {"plan": plan}


def _context_retriever(state: ReviewState, ctx: GraphContext) -> dict:
    if ctx.retriever is None:
        return {"context": ""}
    query = retriever_query(state.get("files", []), state.get("repo", ""))
    try:
        chunks = list(ctx.retriever(query))[:MAX_CONTEXT_CHUNKS]
        return {"context": "\n\n".join(chunk for chunk in chunks if chunk)}
    except Exception as exc:
        # SPECIFICATION §4: empty context on error (log) — never raises.
        _log(f"context_retriever: {exc}")
        error = f"context_retriever: {exc}"
        return {"context": "", "errors": state.get("errors", []) + [error]}


def _make_specialist(
    name: str, ctx: GraphContext
) -> Callable[[ReviewState], dict]:
    _, category = prompts.SPECIALIST_MISSIONS[name]

    def specialist(state: ReviewState) -> dict:
        plan = state.get("plan") or list(SPECIALISTS)
        if name not in plan:
            return {}  # not selected by plan
        user = prompts.specialist_user(
            state.get("diff", ""), state.get("context", "")
        )
        system = prompts.specialist_system(name)
        last_error: Exception | None = None
        for _ in range(RETRY_ATTEMPTS):
            try:
                text = ctx.llm.complete(
                    system, user, temperature=SPECIALIST_TEMPERATURE
                )
                found = parse_findings(text, default_category=category)  # type: ignore[arg-type]
                return {"findings": state.get("findings", []) + found}
            except Exception as exc:
                last_error = exc
        error = f"{name}: failed after {RETRY_ATTEMPTS} attempts: {last_error}"
        return {"errors": state.get("errors", []) + [error]}

    return specialist


def _beats(candidate: Finding, incumbent: Finding) -> bool:
    rank = (
        SEVERITY_RANK[candidate.severity],
        candidate.confidence,
    )
    other = (
        SEVERITY_RANK[incumbent.severity],
        incumbent.confidence,
    )
    return rank < other


def _aggregate(state: ReviewState, ctx: GraphContext) -> dict:
    # aggregate never fails (SPECIFICATION §4) — catch everything.
    try:
        valid: list[Finding] = []
        for item in state.get("findings") or []:
            if isinstance(item, Finding):
                finding = item
            else:
                try:
                    finding = Finding.model_validate(item)
                except Exception:
                    continue
            if (
                ctx.settings.review_severity == "lenient"
                and finding.severity == "info"
            ):
                continue
            valid.append(finding)
        deduped: dict[tuple, Finding] = {}
        for finding in valid:
            key = (finding.file, finding.line, finding.category)
            current = deduped.get(key)
            if current is None or _beats(finding, current):
                deduped[key] = finding
        ordered = sorted(
            deduped.values(),
            key=lambda f: (
                SEVERITY_RANK[f.severity],
                -f.confidence,
                f.file,
                f.line or 0,
                f.title,
            ),
        )
        return {"findings": ordered}
    except Exception as exc:
        _log(f"aggregate degraded ({exc})")
        salvage = [
            item for item in (state.get("findings") or [])
            if isinstance(item, Finding)
        ]
        return {"findings": salvage}


def _deterministic_summary(
    stats: dict[str, int], count: int, errors: list[str]
) -> str:
    counts = ", ".join(f"{n} {sev}" for sev, n in stats.items() if n)
    summary = (
        f"Reviewed changes: {count} finding(s) ({counts or 'none'})."
        if count
        else "Reviewed changes: no issues found."
    )
    if errors:
        summary += f" {len(errors)} node error(s) — see below."
    return summary


def _summarize(
    stats: dict[str, int],
    findings: list[Finding],
    errors: list[str],
    ctx: GraphContext,
) -> str:
    fallback = _deterministic_summary(stats, len(findings), errors)
    try:
        text = ctx.llm.complete(
            prompts.SUMMARIZER_SYSTEM,
            prompts.summarizer_user(
                stats, [f.model_dump() for f in findings], errors
            ),
            temperature=SUMMARY_TEMPERATURE,
        )
        return text.strip() or fallback
    except Exception as exc:
        _log(f"summarizer fallback (deterministic): {exc}")
        return fallback


def _report(state: ReviewState, ctx: GraphContext) -> dict:
    # Failures here abort the run (SPECIFICATION §4 → exit 2).
    findings = [
        item for item in (state.get("findings") or [])
        if isinstance(item, Finding)
    ]
    errors = list(state.get("errors") or [])
    stats = {sev: 0 for sev in SEVERITIES}
    for finding in findings:
        stats[finding.severity] += 1
    review = ReviewReport(
        summary=_summarize(stats, findings, errors, ctx),
        findings=findings,
        stats=stats,
        model=ctx.settings.llm_model,
        trace_url=ctx.tracer.trace_url,
    )
    markdown = render_markdown(review, errors=errors)
    if ctx.output_path:
        Path(ctx.output_path).write_text(
            review.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
    if ctx.record_review is not None:
        try:
            ctx.record_review(review)
        except Exception as exc:  # best effort — must not abort the report
            _log(f"record_review skipped: {exc}")
    return {"report": markdown}


def make_nodes(ctx: GraphContext) -> dict[str, Callable[[ReviewState], dict]]:
    nodes: dict[str, Callable[[ReviewState], dict]] = {
        "start": lambda state: _start(state, ctx),
        "plan": lambda state: _plan(state, ctx),
        "context_retriever": lambda state: _context_retriever(state, ctx),
        "aggregate": lambda state: _aggregate(state, ctx),
        "report": lambda state: _report(state, ctx),
    }
    for name in SPECIALISTS:
        nodes[name] = _make_specialist(name, ctx)
    return nodes


def _wrap(
    name: str,
    fn: Callable[[ReviewState], dict],
    tracer: Tracer,
) -> Callable[[ReviewState], dict]:
    def node(state: ReviewState) -> dict:
        tracer.start_span(name, dict(state))
        try:
            result = fn(state)
        except Exception as exc:
            tracer.end_span(name, error=str(exc))
            raise
        tracer.end_span(name, outputs=result)
        return result

    return node


def build_graph(ctx: GraphContext):
    """Compile the review graph: every node traced, linear edges."""
    graph = StateGraph(ReviewState)
    for node_name, fn in make_nodes(ctx).items():
        graph.add_node(node_name, _wrap(node_name, fn, ctx.tracer))
    graph.add_edge(START, "start")
    for source, target in zip(NODE_ORDER, NODE_ORDER[1:]):
        graph.add_edge(source, target)
    graph.add_edge("report", END)
    return graph.compile()
