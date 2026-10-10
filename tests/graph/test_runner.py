"""Runner tests: exit codes, chunking, artifacts (SPECIFICATION §5/§7)."""

import json

import pytest

from app.models import Finding, ReviewReport
from app.nodes import SPECIALISTS
from app.runner import ReviewError, compute_exit_code, run_review
from app.state import initial_state
from app.tracing import Tracer

BLOCKER_FINDING = json.dumps(
    [
        {
            "file": "app/api.py",
            "line": 3,
            "severity": "blocker",
            "category": "security",
            "title": "SQL injection",
            "detail": "concatenated input reaches execute()",
            "suggestion": "parameterize",
            "confidence": 0.9,
        }
    ]
)


def finding(sev: str) -> Finding:
    return Finding(
        file="a.py", severity=sev, category="bug",  # type: ignore[arg-type]
        title="t", detail="d",
    )


def state_with(findings=(), errors=(), plan=None):
    state = initial_state()
    state["findings"] = list(findings)
    state["errors"] = list(errors)
    state["plan"] = list(plan if plan is not None else SPECIALISTS)
    return state


# --- compute_exit_code -----------------------------------------------------


def test_exit_clean_is_zero() -> None:
    assert compute_exit_code(state_with(findings=[finding("minor")])) == 0
    assert compute_exit_code(state_with()) == 0


def test_exit_blocker_or_major_is_one() -> None:
    assert compute_exit_code(state_with(findings=[finding("blocker")])) == 1
    assert compute_exit_code(state_with(findings=[finding("major")])) == 1


def test_exit_all_specialists_failed_is_two() -> None:
    errors = [f"{name}: failed after 3 attempts: x" for name in SPECIALISTS]
    assert compute_exit_code(state_with(errors=errors)) == 2


def test_exit_partial_failure_uses_findings() -> None:
    errors = ["bug_hunter: failed after 3 attempts: x"]
    assert compute_exit_code(state_with(findings=[finding("major")], errors=errors)) == 1
    assert compute_exit_code(state_with(findings=[], errors=errors)) == 0


def test_exit_empty_plan_defaults_to_findings() -> None:
    assert compute_exit_code(state_with(plan=[], findings=[finding("blocker")])) == 1


# --- run_review ------------------------------------------------------------


def test_run_review_clean_diff_exit_zero(
    settings, fake_llm, clean_diff, tmp_path
) -> None:
    result = run_review(
        clean_diff,
        settings,
        llm=fake_llm,
        tracer=Tracer(None),
        output_path=str(tmp_path / "r.json"),
    )
    assert result.exit_code == 0
    assert result.state["findings"] == []
    assert "0 findings" in result.markdown


def test_run_review_blocker_exit_one(
    settings, make_llm, blocker_diff, tmp_path
) -> None:
    llm = make_llm(responses=[BLOCKER_FINDING] * 4 + ["One blocker."])
    result = run_review(
        blocker_diff,
        settings,
        llm=llm,
        tracer=Tracer(None),
        output_path=str(tmp_path / "r.json"),
    )
    assert result.exit_code == 1
    assert "blocker" in result.markdown


def test_run_review_all_llm_calls_fail_exit_two(
    settings, make_llm, blocker_diff, tmp_path
) -> None:
    llm = make_llm(error=RuntimeError("provider down"))
    result = run_review(
        blocker_diff,
        settings,
        llm=llm,
        tracer=Tracer(None),
        output_path=str(tmp_path / "r.json"),
    )
    assert result.exit_code == 2
    assert result.markdown.startswith("## 🤖")  # report or fail
    assert "Node errors" in result.markdown


def test_run_review_empty_diff_raises(settings, fake_llm) -> None:
    with pytest.raises(ReviewError, match="diff is empty"):
        run_review("", settings, llm=fake_llm, tracer=Tracer(None), output_path=None)


def test_run_review_records_trace_error_then_raises(
    settings, fake_llm, monkeypatch
) -> None:
    tracer = Tracer(None)  # disabled → no network; finish_trace stubbed
    finished = []
    monkeypatch.setattr(tracer, "finish_trace", lambda out: finished.append(out))
    with pytest.raises(ReviewError):
        run_review("  ", settings, llm=fake_llm, tracer=tracer, output_path=None)
    assert finished and "error" in finished[0]


def test_large_diff_accumulates_findings_across_chunks(
    settings_factory, make_llm, tmp_path
) -> None:
    settings = settings_factory(MAX_DIFF_LINES="12")

    def file_diff(name: str) -> str:
        body = "".join(f"+x = {i}\n" for i in range(10))
        return (
            f"diff --git a/{name} b/{name}\n--- a/{name}\n+++ b/{name}\n"
            f"@@ -1,1 +1,10 @@\n{body}"
        )

    diff = file_diff("a.py") + file_diff("b.py")
    finding_a = json.dumps(
        [{"file": "a.py", "line": 1, "severity": "major", "category": "bug",
          "title": "issue a", "detail": "detail a"}]
    )
    finding_b = json.dumps(
        [{"file": "b.py", "line": 2, "severity": "minor", "category": "bug",
          "title": "issue b", "detail": "detail b"}]
    )
    # chunk 1: 4 specialists, chunk 2: 4 specialists, then 2 summaries
    llm = make_llm(
        responses=[finding_a, "[]", "[]", "[]",
                   "[]", finding_b, "[]", "[]",
                   "sum a", "sum b"]
    )
    out = tmp_path / "r.json"
    result = run_review(
        diff, settings, llm=llm, tracer=Tracer(None), output_path=str(out)
    )
    titles = {f.title for f in result.state["findings"]}
    assert titles == {"issue a", "issue b"}
    report = ReviewReport.model_validate_json(out.read_text(encoding="utf-8"))
    assert {f.title for f in report.findings} == {"issue a", "issue b"}


def test_run_review_writes_artifact_and_markdown(
    settings, make_llm, clean_diff, tmp_path
) -> None:
    out = tmp_path / "report.json"
    llm = make_llm(responses=["[]"] * 4 + ["All good."])
    result = run_review(
        clean_diff, settings, llm=llm, tracer=Tracer(None), output_path=str(out)
    )
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) == {
        "summary", "findings", "stats", "model", "trace_url",
    }
    assert result.markdown  # markdown emitted alongside the artifact


def test_run_review_records_findings_when_enabled(
    settings, make_llm, blocker_diff, tmp_path, monkeypatch
) -> None:
    from app import runner

    calls = []
    monkeypatch.setattr(
        runner, "record_review", lambda s, report: calls.append(report)
    )
    llm = make_llm(responses=[BLOCKER_FINDING] * 4 + ["One blocker."])
    run_review(
        blocker_diff,
        settings,
        llm=llm,
        tracer=Tracer(None),
        output_path=str(tmp_path / "r.json"),
        record=True,
    )
    assert len(calls) == 1
    assert calls[0].findings


def test_run_review_no_record_by_default(
    settings, make_llm, blocker_diff, tmp_path, monkeypatch
) -> None:
    from app import runner

    calls = []
    monkeypatch.setattr(
        runner, "record_review", lambda s, report: calls.append(report)
    )
    llm = make_llm(responses=[BLOCKER_FINDING] * 4 + ["One blocker."])
    run_review(
        blocker_diff,
        settings,
        llm=llm,
        tracer=Tracer(None),
        output_path=str(tmp_path / "r.json"),
    )
    assert calls == []
