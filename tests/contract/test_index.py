"""Entry point tests (STEPS.md §1, TESTING.md §1 contract tests)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import index as entry
from app.config import ConfigError
from app.nodes import NODE_ORDER

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_main_prints_model_and_node_list(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("REVIEW_SEVERITY", "normal")

    assert entry.main() == 0

    out = capsys.readouterr().out
    assert "model: gpt-4o-mini" in out
    for node in NODE_ORDER:
        assert node in out


def test_main_returns_2_on_config_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def boom() -> None:
        raise ConfigError("missing LLM_API_KEY")

    monkeypatch.setattr(entry, "load_settings", boom)

    assert entry.main() == 2
    assert "config error" in capsys.readouterr().err


def test_node_order_matches_architecture() -> None:
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


def test_subprocess_success() -> None:
    result = subprocess.run(
        [sys.executable, "index.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={
            **os.environ,
            "LLM_MODEL": "gpt-4o-mini",
            "LLM_API_KEY": "sk-test",
        },
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "model:" in result.stdout
    for node in NODE_ORDER:
        assert node in result.stdout


def test_subprocess_invalid_config_exits_2() -> None:
    env = {**os.environ, "REVIEW_SEVERITY": "extreme"}
    env.pop("LLM_API_KEY", None)
    env.pop("LLM_MODEL", None)
    result = subprocess.run(
        [sys.executable, "index.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=60,
    )
    assert result.returncode == 2
    assert "config error" in result.stderr
