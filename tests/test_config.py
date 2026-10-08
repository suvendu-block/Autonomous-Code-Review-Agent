"""Config loader tests (SPECIFICATION.md §2, TESTING.md §1)."""

import pytest

from app.config import ConfigError, Settings, load_settings

REQUIRED_ENV = {
    "LLM_MODEL": "gpt-4o-mini",
    "LLM_API_KEY": "sk-test",
    "LANGSMITH_API_KEY": "",
    "LANGSMITH_PROJECT": "code-review-agent",
    "CHROMA_PATH": "./.chroma",
    "EMBEDDING_MODEL": "text-embedding-3-small",
    "MAX_DIFF_LINES": "3000",
    "REVIEW_SEVERITY": "normal",
}


def make_settings(monkeypatch: pytest.MonkeyPatch, **overrides: str) -> Settings:
    for key, value in {**REQUIRED_ENV, **overrides}.items():
        monkeypatch.setenv(key, value)
    return load_settings(env_file=None)


def test_valid_config_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = make_settings(monkeypatch)
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.review_severity == "normal"
    assert settings.max_diff_lines == 3000
    assert settings.langsmith_api_key is None
    assert settings.langsmith_project == "code-review-agent"
    assert settings.chroma_path == "./.chroma"
    assert settings.embedding_model == "text-embedding-3-small"


def test_missing_llm_model_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    with pytest.raises(ConfigError) as exc:
        load_settings(env_file=None)
    assert "llm_model" in str(exc.value)


def test_missing_llm_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ConfigError) as exc:
        load_settings(env_file=None)
    assert "llm_api_key" in str(exc.value)


@pytest.mark.parametrize("mode", ["strict", "normal", "lenient"])
def test_severity_modes_accepted(
    monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    assert make_settings(monkeypatch, REVIEW_SEVERITY=mode).review_severity == mode


def test_invalid_severity_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfigError) as exc:
        make_settings(monkeypatch, REVIEW_SEVERITY="extreme")
    assert "review_severity" in str(exc.value)


def test_non_integer_max_diff_lines_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ConfigError) as exc:
        make_settings(monkeypatch, MAX_DIFF_LINES="lots")
    assert "max_diff_lines" in str(exc.value)


def test_zero_max_diff_lines_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfigError) as exc:
        make_settings(monkeypatch, MAX_DIFF_LINES="0")
    assert "max_diff_lines" in str(exc.value)


def test_dotenv_file_is_read(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_MODEL=gpt-4o-mini\n"
        "LLM_API_KEY=sk-from-dotenv\n"
        "REVIEW_SEVERITY=strict\n",
        encoding="utf-8",
    )
    for key in REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)

    settings = load_settings(env_file=str(env_file))
    assert settings.llm_api_key == "sk-from-dotenv"
    assert settings.review_severity == "strict"
