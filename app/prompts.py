"""Prompts for the specialist agents and the summarizer.

Determinism (PRINCIPLES.md §4): specialists run at temperature 0 and must
answer with machine-parseable JSON only — schema lives here so a prompt
change is a reviewable diff.
"""

from __future__ import annotations

import json

SPECIALIST_SYSTEM = """\
You are the {role} in an autonomous code review pipeline. You review unified
diffs only — never invent files or lines that are not in the diff.

Respond with ONLY a JSON array (no prose, no markdown fences). Each element:
{{
  "file": "<path from the diff>",
  "line": <int or null>,
  "severity": "blocker" | "major" | "minor" | "info",
  "category": "{category}",
  "title": "<short issue title>",
  "detail": "<evidence: what and why, referencing the code>",
  "suggestion": "<concrete fix or null>",
  "confidence": <0.0..1.0>
}}
Return [] when the diff contains no issues in your area. Never pad findings.
"""

SPECIALIST_MISSIONS = {
    "bug_hunter": ("logic error, edge case, race condition or correctness bug hunter", "bug"),
    "security_auditor": ("security auditor for injection, secrets and unsafe deserialization", "security"),
    "style_linter": ("style linter for naming, structure and project conventions", "style"),
    "test_gap_analyzer": ("test gap analyzer for untested paths and missing cases", "testing"),
}


def specialist_system(name: str) -> str:
    role, category = SPECIALIST_MISSIONS[name]
    return SPECIALIST_SYSTEM.format(role=role, category=category)


def specialist_user(diff: str, context: str) -> str:
    parts = []
    if context.strip():
        parts.append("# Project context\n" + context.strip())
    parts.append("# Unified diff\n" + diff)
    return "\n\n".join(parts)


SUMMARIZER_SYSTEM = """\
You summarize an automated code review in 1-2 plain sentences: scope reviewed
and headline risk. No markdown, no lists, no leading 'Summary:' label."""

SUMMARIZER_USER = "Review stats and top findings (JSON):\n{payload}"


def summarizer_user(stats: dict, findings: list[dict], errors: list[str]) -> str:
    payload = json.dumps(
        {"stats": stats, "top_findings": findings[:5], "node_errors": errors},
        indent=2,
    )
    return SUMMARIZER_USER.format(payload=payload)
