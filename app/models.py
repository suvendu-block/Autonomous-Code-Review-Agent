"""Data contracts (SPECIFICATION.md §3).

The only shapes allowed to cross a node boundary (PRINCIPLES.md §5).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["blocker", "major", "minor", "info"]
Category = Literal["bug", "security", "style", "testing", "docs", "performance"]


class Finding(BaseModel):
    file: str
    line: int | None = None
    severity: Severity
    category: Category
    title: str
    detail: str
    suggestion: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ReviewReport(BaseModel):
    summary: str
    findings: list[Finding]
    stats: dict[str, int]
    model: str
    trace_url: str | None = None
