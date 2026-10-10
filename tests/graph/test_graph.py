"""Graph wiring and node-failure tests (TESTING.md §2, SPECIFICATION §4)."""

import json

import pytest

from app import nodes
from app.nodes import (
    NODE_ORDER,
    SPECIALISTS,
    StartError,
    build_graph,
    decide_specialists,
)
from app.state import initial_state

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


def invoke(ctx, diff: str):
    return build_graph(ctx).invoke(initial_state(diff=diff))


def test_node_order_matches_registry() -> None:
    assert NODE_ORDER == [
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


def test_happy_path_produces_report(make_ctx, make_llm, blocker_diff) -> None:
    llm = make_llm(responses=[BLOCKER_FINDING] * 4 + ["One blocker found."])
    state = invoke(make_ctx(llm), blocker_diff)
    assert state["plan"] == list(SPECIALISTS)
    assert len(state["findings"]) == 1
    assert state["findings"][0].severity == "blocker"
    assert state["errors"] == []
    assert state["report"].startswith("## 🤖 Autonomous Review — 1 findings")
    assert "SQL injection" in state["report"]


def test_start_aborts_on_empty_diff(make_ctx, fake_llm) -> None:
    with pytest.raises(StartError, match="diff is empty"):
        invoke(make_ctx(fake_llm), "   \n  ")


def test_plan_fallback_runs_all_specialists(
    make_ctx, fake_llm, blocker_diff, monkeypatch
) -> None:
    def boom(files, diff):
        raise RuntimeError("planner exploded")

    monkeypatch.setattr(nodes, "decide_specialists", boom)
    state = invoke(make_ctx(fake_llm), blocker_diff)
    assert state["plan"] == list(SPECIALISTS)


def test_plan_skips_test_analyzer_for_docs(
    make_ctx, fake_llm, docs_diff
) -> None:
    state = invoke(make_ctx(fake_llm), docs_diff)
    assert state["plan"] == ["bug_hunter", "security_auditor", "style_linter"]
    assert "test_gap_analyzer" not in state["plan"]


def test_unplanned_specialist_does_not_call_llm(
    make_ctx, make_llm, docs_diff
) -> None:
    llm = make_llm()
    invoke(make_ctx(llm), docs_diff)
    systems = " ".join(call["system"] for call in llm.calls)
    assert "test gap" not in systems.lower()


def test_specialist_retries_twice_then_records_error(
    make_ctx, make_llm, blocker_diff
) -> None:
    llm = make_llm(error=RuntimeError("provider down"))
    state = invoke(make_ctx(llm), blocker_diff)
    assert state["findings"] == []
    specialist_calls = [
        c for c in llm.calls if c["temperature"] == 0.0
    ]
    # 4 specialists × (1 + 2 retries)
    assert len(specialist_calls) == 4 * 3
    recorded = [e for e in state["errors"] if ":" in e]
    assert len(recorded) == 4
    for name in SPECIALISTS:
        assert any(e.startswith(f"{name}:") for e in state["errors"])
    # report-or-fail: markdown still produced
    assert state["report"].startswith("## 🤖")
    assert "Node errors" in state["report"]


def test_specialist_partial_failure(make_ctx, make_llm, blocker_diff) -> None:
    # bug_hunter succeeds on its first attempt; the three remaining
    # specialists fail all three attempts; summarizer still runs.
    sequence = [BLOCKER_FINDING]
    sequence += [RuntimeError("nope")] * (3 * 3)
    sequence.append("summary")
    llm = make_llm(responses=sequence)
    state = invoke(make_ctx(llm), blocker_diff)
    assert len(state["findings"]) == 1
    failed = [e for e in state["errors"] if e.endswith("nope")]
    assert len(failed) == 3
    assert state["report"].startswith("## 🤖")


def test_retriever_error_degrades_to_empty_context(
    make_ctx, make_llm, blocker_diff
) -> None:
    def broken(query):
        raise RuntimeError("chroma offline")

    state = invoke(make_ctx(make_llm(), retriever=broken), blocker_diff)
    assert state["context"] == ""
    assert any(e.startswith("context_retriever:") for e in state["errors"])
    assert state["report"].startswith("## 🤖")  # run continued


def test_retriever_success_feeds_context(
    make_ctx, make_llm, blocker_diff
) -> None:
    state = invoke(
        make_ctx(make_llm(), retriever=lambda q: ["rule: use params", "x"] * 9),
        blocker_diff,
    )
    assert "rule: use params" in state["context"]
    assert state["context"].count("rule: use params") <= 8


def test_aggregate_dedupes_by_file_line_category(make_ctx) -> None:
    from app.models import Finding

    a = Finding(
        file="a.py", line=1, severity="minor", category="bug",
        title="t", detail="d", confidence=0.4,
    )
    b = Finding(
        file="a.py", line=1, severity="blocker", category="bug",
        title="t2", detail="d2", confidence=0.9,
    )
    c = Finding(
        file="a.py", line=1, severity="minor", category="style",
        title="t3", detail="d3",
    )
    state = {"findings": [a, b, c]}
    result = nodes._aggregate(state, make_ctx())
    findings = result["findings"]
    assert len(findings) == 2  # (a.py,1,bug) + (a.py,1,style)
    assert findings[0].severity == "blocker"  # sorted by severity


def test_aggregate_sorts_by_severity_then_confidence(make_ctx) -> None:
    from app.models import Finding

    def f(sev, conf, line):
        return Finding(
            file="a.py", line=line, severity=sev, category="bug",
            title="t", detail="d", confidence=conf,
        )

    state = {
        "findings": [
            f("info", 1.0, 1),
            f("major", 0.2, 2),
            f("blocker", 0.1, 3),
            f("major", 0.9, 4),
        ]
    }
    order = [
        (x.severity, x.confidence)
        for x in nodes._aggregate(state, make_ctx())["findings"]
    ]
    assert order == [
        ("blocker", 0.1),
        ("major", 0.9),
        ("major", 0.2),
        ("info", 1.0),
    ]


def test_aggregate_never_raises_on_garbage(make_ctx) -> None:
    from app.models import Finding

    valid = Finding(
        file="a.py", severity="info", category="docs", title="t", detail="d"
    )
    state = {"findings": [{"bad": 1}, None, 42, {"file": "b.py"}, valid]}
    result = nodes._aggregate(state, make_ctx())
    assert result["findings"] == [valid]


def test_aggregate_lenient_drops_info(make_ctx, settings_factory) -> None:
    from app.models import Finding

    settings = settings_factory(REVIEW_SEVERITY="lenient")
    ctx = make_ctx(settings_override=settings)
    state = {
        "findings": [
            Finding(file="a.py", severity="info", category="docs", title="t", detail="d"),
            Finding(file="b.py", severity="major", category="bug", title="t", detail="d"),
        ]
    }
    result = nodes._aggregate(state, ctx)
    assert [f.severity for f in result["findings"]] == ["major"]


def test_determinism_same_input_same_findings(
    make_ctx, make_llm, blocker_diff
) -> None:
    responses = lambda: [BLOCKER_FINDING] * 4 + ["Summary."]  # noqa: E731
    first = invoke(make_ctx(make_llm(responses=responses())), blocker_diff)
    second = invoke(make_ctx(make_llm(responses=responses())), blocker_diff)
    assert first["findings"] == second["findings"]
    assert first["report"] == second["report"]


def test_temperatures_specialists_zero_summary_point_two(
    make_ctx, make_llm, blocker_diff
) -> None:
    llm = make_llm(responses=[BLOCKER_FINDING] * 4 + ["Summary."])
    invoke(make_ctx(llm), blocker_diff)
    assert len(llm.calls) == 5
    assert llm.temperatures[:4] == [0.0, 0.0, 0.0, 0.0]
    assert llm.temperatures[4] == 0.2


def test_report_writes_json_artifact(
    make_ctx, make_llm, blocker_diff, tmp_path
) -> None:
    from app.models import ReviewReport

    out = tmp_path / "review_report.json"
    llm = make_llm(responses=[BLOCKER_FINDING] * 4 + ["Summary."])
    state = invoke(make_ctx(llm, output_path=str(out)), blocker_diff)
    assert out.exists()
    report = ReviewReport.model_validate_json(out.read_text(encoding="utf-8"))
    assert len(report.findings) == 1
    assert report.stats["blocker"] == 1
    assert report.model == "gpt-4o-mini"
    assert "SQL injection" in state["report"]


def test_report_failure_aborts_run(
    make_ctx, make_llm, blocker_diff, tmp_path
) -> None:
    impossible = tmp_path / "no-such-dir" / "nested" / "r.json"
    llm = make_llm(responses=[BLOCKER_FINDING] * 4 + ["Summary."])
    with pytest.raises(Exception, match="no-such-dir|eno|not find|path"):
        invoke(make_ctx(llm, output_path=str(impossible)), blocker_diff)


def test_report_embeds_trace_url(make_ctx, make_llm, blocker_diff) -> None:
    from app.tracing import Tracer

    tracer = Tracer(None)
    tracer.trace_url = "https://smith.example/projects/p/1/r/root"
    llm = make_llm(responses=[BLOCKER_FINDING] * 4 + ["Summary."])
    state = invoke(make_ctx(llm, tracer=tracer), blocker_diff)
    assert "https://smith.example/projects/p/1/r/root" in state["report"]


def test_decide_specialists_matrix() -> None:
    assert decide_specialists(["a.py"], "") == list(SPECIALISTS)
    assert decide_specialists(["README.md"], "") == [
        "bug_hunter", "security_auditor", "style_linter",
    ]
    assert decide_specialists([], "") == list(SPECIALISTS)
