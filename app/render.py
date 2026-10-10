"""Render the final markdown PR comment (SPECIFICATION.md §6)."""

from __future__ import annotations

from collections.abc import Sequence

from app.models import ReviewReport

HEADER = "## 🤖 Autonomous Review — {count} findings"


def _location(file: str, line: int | None) -> str:
    return f"{file}:{line}" if line is not None else file


def render_markdown(
    review: ReviewReport, *, errors: Sequence[str] = ()
) -> str:
    """Render ``review`` as the markdown PR comment.

    ``errors`` are node failures recorded in ``ReviewState.errors`` — the
    report must surface them (PRINCIPLES.md §1: report or fail, never silence).
    """
    lines: list[str] = [HEADER.format(count=len(review.findings)), ""]
    lines.append(review.summary.strip() or "No issues found.")
    lines.append("")

    if review.findings:
        lines += [
            "| # | Severity | File | Issue |",
            "|---|----------|------|-------|",
        ]
        for i, f in enumerate(review.findings, start=1):
            lines.append(
                f"| {i} | {f.severity} | {_location(f.file, f.line)} | {f.title} |"
            )
        lines += ["", "### Details"]
        for i, f in enumerate(review.findings, start=1):
            lines.append(
                f"{i}. **[{f.severity}] {_location(f.file, f.line)}** — {f.title}"
            )
            lines.append(f"   {f.detail}")
            if f.suggestion:
                lines.append(f"   _Suggestion:_ {f.suggestion}")

    if errors:
        lines += ["", "### ⚠️ Node errors"]
        lines += [f"- {e}" for e in errors]

    footer = f"_Model: {review.model}_"
    if review.trace_url:
        footer += f" · [trace]({review.trace_url})"
    lines += ["", footer]
    return "\n".join(lines)
