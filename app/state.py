"""Shared graph state (ARCHITECTURE.md — State section).

``ReviewState`` is a TypedDict shared across nodes (LangGraph checkpointing
friendly). ``Finding`` / ``ReviewReport`` are the only shapes that cross a
node boundary (PRINCIPLES.md §5).
"""

from __future__ import annotations

from typing import TypedDict

from app.models import Finding


class ReviewState(TypedDict):
    repo: str
    diff: str
    files: list[str]
    plan: list[str]
    context: str
    findings: list[Finding]
    report: str
    errors: list[str]


def initial_state(repo: str = "", diff: str = "") -> ReviewState:
    """Fresh state for one graph invocation."""
    return {
        "repo": repo,
        "diff": diff,
        "files": [],
        "plan": [],
        "context": "",
        "findings": [],
        "report": "",
        "errors": [],
    }
