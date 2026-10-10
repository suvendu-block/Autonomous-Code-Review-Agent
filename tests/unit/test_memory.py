"""ChromaDB memory tests (ARCHITECTURE.md — Memory layer, STEPS §4)."""

import pytest

from app.memory import (
    COLLECTIONS,
    MAX_CONTEXT_CHUNKS,
    chunk_text,
    ingest_repo,
    record_review,
    retrieve,
)
from app.models import Finding, ReviewReport


def fake_embedder(texts: list[str]) -> list[list[float]]:
    return [
        [float((sum(map(ord, text)) + i) % 13) for i in range(16)]
        for text in texts
    ]


@pytest.fixture
def chroma_settings(settings_factory, tmp_path):
    return settings_factory(CHROMA_PATH=str(tmp_path / "chroma"))


def write_repo(root):
    (root / "README.md").write_text("# Project\nDocs here.\n", encoding="utf-8")
    (root / "CONTRIBUTING.md").write_text(
        "Use black and type hints.\n", encoding="utf-8"
    )
    (root / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n", encoding="utf-8")
    (root / "review_report.json").write_text('{"summary": "past"}', encoding="utf-8")
    (root / "main.py").write_text("print('hi')\n", encoding="utf-8")  # not ingested


def test_chunk_text_respects_size(tmp_path) -> None:
    text = "\n".join(f"line {i}" for i in range(200))
    chunks = chunk_text(text, size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)
    assert all(c.strip() for c in chunks)


def test_ingest_creates_all_collections(chroma_settings, tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_repo(repo)
    counts = ingest_repo(repo, chroma_settings, embedder=fake_embedder)
    assert set(counts) == set(COLLECTIONS)
    assert counts["codebase_docs"] > 0
    assert counts["project_conventions"] > 0
    assert counts["past_reviews"] > 0


def test_ingest_skips_code_files(chroma_settings, tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_repo(repo)
    counts = ingest_repo(repo, chroma_settings, embedder=fake_embedder)
    assert counts["codebase_docs"] == 1  # README only
    assert counts["project_conventions"] == 2  # CONTRIBUTING + pyproject
    assert counts["past_reviews"] == 1
    assert counts["codebase_docs"] + counts["project_conventions"] + counts["past_reviews"] == 4


def test_ingest_missing_dir_raises(chroma_settings, tmp_path) -> None:
    with pytest.raises(NotADirectoryError):
        ingest_repo(tmp_path / "nope", chroma_settings, embedder=fake_embedder)


def test_retrieve_returns_at_most_8(chroma_settings, tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text(
        "\n".join(f"doc chunk {i} about conventions" for i in range(30)),
        encoding="utf-8",
    )
    ingest_repo(repo, chroma_settings, embedder=fake_embedder)
    chunks = retrieve(
        chroma_settings, "conventions", embedder=fake_embedder
    )
    assert 0 < len(chunks) <= MAX_CONTEXT_CHUNKS


def test_retrieve_empty_store(chroma_settings) -> None:
    assert retrieve(chroma_settings, "query", embedder=fake_embedder) == []


def test_record_review_adds_to_past_reviews(chroma_settings) -> None:
    report = ReviewReport(
        summary="s",
        findings=[
            Finding(
                file="a.py",
                line=1,
                severity="blocker",
                category="security",
                title="injection",
                detail="raw sql",
            )
        ],
        stats={"blocker": 1},
        model="m",
    )
    added = record_review(chroma_settings, report, embedder=fake_embedder)
    assert added == 1
    past = retrieve(chroma_settings, "injection", embedder=fake_embedder)
    assert any("injection" in chunk for chunk in past)


def test_record_review_empty_findings_noop(chroma_settings) -> None:
    report = ReviewReport(summary="s", findings=[], stats={}, model="m")
    assert record_review(chroma_settings, report, embedder=fake_embedder) == 0
