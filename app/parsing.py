"""Parse specialist LLM output into validated ``Finding`` models.

Raw model text is untrusted: it may arrive fenced, wrapped in an object, or
with sloppy enum values. Coercion is applied here (never on the contracts
themselves, which stay strict — SPECIFICATION.md §3). Anything unparseable
raises so the caller can retry ×2 (SPECIFICATION.md §4).
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.models import Category, Finding, Severity

SEVERITY_ALIASES: dict[str, Severity] = {
    "blocker": "blocker",
    "critical": "blocker",
    "major": "major",
    "error": "major",
    "high": "major",
    "minor": "minor",
    "warning": "minor",
    "warn": "minor",
    "medium": "minor",
    "info": "info",
    "note": "info",
    "low": "info",
    "hint": "info",
}

CATEGORIES: tuple[str, ...] = (
    "bug", "security", "style", "testing", "docs", "performance",
)

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class ParseError(ValueError):
    """Response could not be turned into any valid finding."""


def _extract_json(text: str) -> Any:
    fenced = _FENCE_RE.search(text)
    if fenced:
        text = fenced.group(1)
    text = text.strip()
    if not text:
        raise ParseError("empty response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Tolerate prose around a JSON array/object payload.
    for opener, closer in (("[", "]"), ("{", "}")):
        start, end = text.find(opener), text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ParseError("response is not JSON")


def _coerce_severity(value: Any) -> Severity | None:
    if isinstance(value, str):
        return SEVERITY_ALIASES.get(value.strip().lower())
    return None


def _coerce_line(value: Any) -> int | None:
    if value is None or value is False:
        return None
    try:
        line = int(value)
    except (TypeError, ValueError):
        return None
    return line if line >= 0 else None


def _coerce_confidence(value: Any) -> float:
    try:
        conf = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, conf))


def _coerce_finding(raw: Any, default_category: Category) -> Finding | None:
    if not isinstance(raw, dict):
        return None
    title = str(raw.get("title") or "").strip()
    detail = str(raw.get("detail") or "").strip()
    file = str(raw.get("file") or "").strip()
    if not (title and detail and file):
        return None
    severity = _coerce_severity(raw.get("severity"))
    if severity is None:
        return None
    category_raw = str(raw.get("category") or "").strip().lower()
    category = category_raw if category_raw in CATEGORIES else default_category
    suggestion = str(raw.get("suggestion") or "").strip() or None
    try:
        return Finding(
            file=file,
            line=_coerce_line(raw.get("line")),
            severity=severity,
            category=category,  # type: ignore[arg-type]
            title=title,
            detail=detail,
            suggestion=suggestion,
            confidence=_coerce_confidence(raw.get("confidence", 0.5)),
        )
    except ValidationError:
        return None


def parse_findings(text: str, default_category: Category) -> list[Finding]:
    """Parse model text into findings; raise :class:`ParseError` on garbage.

    An empty JSON array is a valid answer ("no findings"). A payload where
    every entry is invalid raises so the specialist can retry.
    """
    data = _extract_json(text)
    if isinstance(data, dict):
        for key in ("findings", "results", "issues"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = [data] if "file" in data else None
    if data is None or not isinstance(data, list):
        raise ParseError("expected a JSON array of findings")
    if not data:
        return []
    findings: list[Finding] = []
    for raw in data:
        finding = _coerce_finding(raw, default_category)
        if finding is not None:
            findings.append(finding)
    if not findings:
        raise ParseError("no valid findings in response")
    return findings
