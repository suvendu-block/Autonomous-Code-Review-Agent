"""Specialist output parsing tests (SPECIFICATION §3/§4)."""

import pytest

from app.parsing import ParseError, parse_findings

VALID = {
    "file": "app/api.py",
    "line": 12,
    "severity": "major",
    "category": "bug",
    "title": "off-by-one",
    "detail": "range stops early",
    "suggestion": "use <= n",
    "confidence": 0.7,
}


def test_plain_array() -> None:
    import json

    findings = parse_findings(json.dumps([VALID]), default_category="bug")
    assert len(findings) == 1
    assert findings[0].title == "off-by-one"
    assert findings[0].severity == "major"


def test_fenced_array() -> None:
    text = "```json\n[{\"file\": \"a.py\", \"severity\": \"info\", \"category\": \"style\",\n\"title\": \"t\", \"detail\": \"d\"}]\n```"
    findings = parse_findings(text, default_category="style")
    assert findings[0].file == "a.py"


def test_wrapped_object_takes_findings_key() -> None:
    text = '{"findings": [{"file": "a.py", "severity": "minor", "category": "bug", "title": "t", "detail": "d"}]}'
    assert len(parse_findings(text, default_category="bug")) == 1


def test_prose_around_array() -> None:
    text = 'Here you go: [{"file": "a.py", "severity": "info", "category": "docs", "title": "typo", "detail": "speling"}] hope that helps'
    assert len(parse_findings(text, default_category="docs")) == 1


def test_empty_array_is_valid_no_findings() -> None:
    assert parse_findings("[]", default_category="bug") == []


def test_severity_aliases() -> None:
    text = '[{"file": "a.py", "severity": "CRITICAL", "category": "bug", "title": "t", "detail": "d"}]'
    assert parse_findings(text, default_category="bug")[0].severity == "blocker"


def test_default_category_applied_when_invalid() -> None:
    text = '[{"file": "a.py", "severity": "minor", "category": "whatever", "title": "t", "detail": "d"}]'
    assert parse_findings(text, default_category="security")[0].category == "security"


def test_confidence_clamped() -> None:
    text = '[{"file": "a.py", "severity": "minor", "category": "bug", "title": "t", "detail": "d", "confidence": 3.5}]'
    assert parse_findings(text, default_category="bug")[0].confidence == 1.0


def test_garbage_raises() -> None:
    with pytest.raises(ParseError):
        parse_findings("I could not review this diff, sorry.", default_category="bug")


def test_all_invalid_entries_raise() -> None:
    with pytest.raises(ParseError):
        parse_findings('[{"severity": "blocker"}]', default_category="bug")


def test_invalid_entries_dropped_when_others_valid() -> None:
    text = '[{"severity": "blocker"}, {"file": "a.py", "severity": "major", "category": "bug", "title": "ok", "detail": "ok"}]'
    findings = parse_findings(text, default_category="bug")
    assert len(findings) == 1
    assert findings[0].title == "ok"


def test_line_coercion() -> None:
    text = '[{"file": "a.py", "line": "42", "severity": "major", "category": "bug", "title": "t", "detail": "d"}]'
    assert parse_findings(text, default_category="bug")[0].line == 42
