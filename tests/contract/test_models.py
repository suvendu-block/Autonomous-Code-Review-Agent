"""Contract tests (SPECIFICATION.md §3, TESTING.md §1)."""

import pytest
from pydantic import ValidationError

from app.models import Finding, ReviewReport


def make_finding(**overrides) -> Finding:
    base = dict(
        file="app/api.py",
        line=42,
        severity="blocker",
        category="security",
        title="SQL built from user input",
        detail="String concatenation reaches execute().",
        suggestion="Use a parameterized query.",
        confidence=0.9,
    )
    base.update(overrides)
    return Finding(**base)


def test_valid_finding_fields() -> None:
    f = make_finding()
    assert f.severity == "blocker"
    assert f.category == "security"
    assert f.confidence == 0.9
    assert f.line == 42
    assert f.suggestion.startswith("Use a parameterized")


def test_optional_defaults() -> None:
    f = Finding(
        file="a.py",
        severity="info",
        category="style",
        title="naming",
        detail="x",
    )
    assert f.line is None
    assert f.suggestion is None
    assert f.confidence == 0.5


@pytest.mark.parametrize("bad", ["critical", "BLOCKER", ""])
def test_invalid_severity_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        make_finding(severity=bad)


@pytest.mark.parametrize("bad", ["buggy", "SECURITY", ""])
def test_invalid_category_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        make_finding(category=bad)


@pytest.mark.parametrize("bad", [-0.1, 1.1])
def test_confidence_bounds(bad: float) -> None:
    with pytest.raises(ValidationError):
        make_finding(confidence=bad)


@pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
def test_confidence_edges_accepted(value: float) -> None:
    assert make_finding(confidence=value).confidence == value


def test_finding_json_keys_match_spec() -> None:
    assert set(make_finding().model_dump()) == {
        "file",
        "line",
        "severity",
        "category",
        "title",
        "detail",
        "suggestion",
        "confidence",
    }


def test_report_valid() -> None:
    r = ReviewReport(
        summary="2 issues",
        findings=[make_finding(), make_finding(severity="minor")],
        stats={"blocker": 1, "minor": 1},
        model="gpt-4o-mini",
    )
    assert len(r.findings) == 2
    assert r.trace_url is None
    assert r.stats["blocker"] == 1


def test_report_requires_stats() -> None:
    with pytest.raises(ValidationError):
        ReviewReport(summary="x", findings=[], model="m")


def test_report_roundtrip() -> None:
    r = ReviewReport(
        summary="s",
        findings=[make_finding()],
        stats={"blocker": 1},
        model="gpt-4o-mini",
        trace_url="https://smith.example/t/1",
    )
    assert ReviewReport.model_validate_json(r.model_dump_json()) == r
