"""CLI contract tests (SPECIFICATION §7 — exit codes 0 | 1 | 2)."""

from __future__ import annotations

import io
import json
import sys

import pytest

import index as entry
from app.config import ConfigError
from app.runner import ReviewResult, run_review as real_run_review
from app.state import initial_state


def review_result(exit_code: int) -> ReviewResult:
    state = initial_state()
    state["report"] = "## 🤖 Autonomous Review — 0 findings"
    return ReviewResult(state=state, markdown=state["report"], exit_code=exit_code)


@pytest.fixture
def loaded(settings, monkeypatch):
    """Run CLI commands against isolated settings (no .env dependency)."""
    monkeypatch.setattr(entry, "load_settings", lambda: settings)
    return settings


def make_patch(tmp_path, name="d.patch", content="diff --git a/a.py b/a.py\n+++ b/a.py\n"):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_unknown_command_exits_2(capsys) -> None:
    assert entry.main(["frobnicate"]) == 2
    assert "unknown command" in capsys.readouterr().err


def test_help_exits_0(capsys) -> None:
    assert entry.main(["--help"]) == 0
    out = capsys.readouterr().out
    assert "usage:" in out
    assert "review <diff|->" in out
    assert "exit codes" in out


def test_review_missing_diff_file_exits_2(tmp_path, capsys, loaded) -> None:
    assert entry.main(["review", str(tmp_path / "nope.patch")]) == 2
    assert "diff read error" in capsys.readouterr().err


def test_review_empty_diff_exits_2(tmp_path, capsys, loaded) -> None:
    empty = tmp_path / "empty.patch"
    empty.write_text("  \n", encoding="utf-8")
    assert entry.main(["review", str(empty)]) == 2
    assert "diff is empty" in capsys.readouterr().err


def test_review_config_error_exits_2(monkeypatch, capsys) -> None:
    def boom() -> None:
        raise ConfigError("missing LLM_API_KEY")

    monkeypatch.setattr(entry, "load_settings", boom)
    assert entry.main(["review", "whatever.patch"]) == 2
    assert "config error" in capsys.readouterr().err


def test_review_passes_exit_code_through(
    monkeypatch, tmp_path, capsys, loaded
) -> None:
    diff = make_patch(tmp_path)
    captured = {}

    def fake_run_review(diff_text, settings, **kwargs):
        captured["diff"] = diff_text
        captured["kwargs"] = kwargs
        return review_result(1)

    monkeypatch.setattr("app.runner.run_review", fake_run_review)
    code = entry.main(["review", str(diff), "--repo", "my/repo"])
    assert code == 1
    assert captured["diff"].startswith("diff --git")
    assert captured["kwargs"]["repo"] == "my/repo"
    assert "Autonomous Review" in capsys.readouterr().out


def test_review_stdout_is_markdown_and_errors_to_stderr(
    monkeypatch, tmp_path, capsys, loaded
) -> None:
    diff = make_patch(tmp_path)

    def fake_run_review(diff_text, settings, **kwargs):
        result = review_result(0)
        result.state["errors"].append("bug_hunter: boom")
        return result

    monkeypatch.setattr("app.runner.run_review", fake_run_review)
    assert entry.main(["review", str(diff)]) == 0
    out, err = capsys.readouterr()
    assert "Autonomous Review" in out
    assert "node error: bug_hunter: boom" in err


def test_review_stdin(monkeypatch, capsys, loaded) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("diff --git a/a.py b/a.py\n"))
    captured = {}

    def fake_run_review(diff_text, settings, **kwargs):
        captured["diff"] = diff_text
        return review_result(0)

    monkeypatch.setattr("app.runner.run_review", fake_run_review)
    assert entry.main(["review", "-"]) == 0
    assert captured["diff"].startswith("diff --git")


def test_review_end_to_end_with_stubbed_llm(
    monkeypatch, tmp_path, capsys, settings_factory, make_llm
) -> None:
    """Full CLI path: argparse → settings → graph → artifact + exit code."""
    settings = settings_factory(CHROMA_PATH=str(tmp_path / "no-chroma"))
    monkeypatch.setattr(entry, "load_settings", lambda: settings)

    diff = make_patch(
        tmp_path,
        name="d.patch",
        content=(
            "diff --git a/app/api.py b/app/api.py\n"
            "--- a/app/api.py\n"
            "+++ b/app/api.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        ),
    )
    out = tmp_path / "report.json"

    def with_fake_llm(diff_text, settings_arg, **kwargs):
        kwargs["llm"] = make_llm()
        return real_run_review(diff_text, settings_arg, **kwargs)

    monkeypatch.setattr("app.runner.run_review", with_fake_llm)
    code = entry.main(["review", str(diff), "-o", str(out), "--no-record"])
    assert code == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["stats"] == {"blocker": 0, "major": 0, "minor": 0, "info": 0}
    assert report["model"] == "gpt-4o-mini"
    assert "Autonomous Review" in capsys.readouterr().out
