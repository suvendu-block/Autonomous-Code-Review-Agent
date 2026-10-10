"""Markdown renderer contract tests (SPECIFICATION §6)."""

from app.models import Finding, ReviewReport
from app.render import render_markdown


def make_report(**overrides) -> ReviewReport:
    base = dict(
        summary="2 issues found.",
        findings=[
            Finding(
                file="security/api.py",
                line=42,
                severity="blocker",
                category="security",
                title="SQL string built from user input",
                detail="Concatenated input reaches execute().",
                suggestion="Use a parameterized query.",
                confidence=0.9,
            ),
            Finding(
                file="app/utils.py",
                severity="minor",
                category="style",
                title="naming",
                detail="unclear name",
            ),
        ],
        stats={"blocker": 1, "minor": 1},
        model="gpt-4o-mini",
    )
    base.update(overrides)
    return ReviewReport(**base)


def test_header_matches_spec() -> None:
    md = render_markdown(make_report())
    assert md.startswith("## 🤖 Autonomous Review — 2 findings")


def test_table_rows() -> None:
    md = render_markdown(make_report())
    assert "| # | Severity | File | Issue |" in md
    assert "| 1 | blocker | security/api.py:42 | SQL string built from user input |" in md
    assert "| 2 | minor | app/utils.py | naming |" in md


def test_details_with_and_without_suggestion() -> None:
    md = render_markdown(make_report())
    assert "1. **[blocker] security/api.py:42** — SQL string built from user input" in md
    assert "_Suggestion:_ Use a parameterized query." in md
    assert "2. **[minor] app/utils.py** — naming" in md
    assert md.count("_Suggestion:_") == 1


def test_summary_included() -> None:
    md = render_markdown(make_report())
    assert "2 issues found." in md


def test_errors_section() -> None:
    md = render_markdown(make_report(), errors=["bug_hunter: boom"])
    assert "### ⚠️ Node errors" in md
    assert "- bug_hunter: boom" in md


def test_no_errors_section_when_clean() -> None:
    assert "Node errors" not in render_markdown(make_report())


def test_trace_footer() -> None:
    md = render_markdown(make_report(trace_url="https://smith.example/t/1"))
    assert "[trace](https://smith.example/t/1)" in md


def test_empty_findings() -> None:
    md = render_markdown(
        make_report(findings=[], stats={}, summary="No issues found.")
    )
    assert "— 0 findings" in md
    assert "No issues found." in md
    assert "| # |" not in md
