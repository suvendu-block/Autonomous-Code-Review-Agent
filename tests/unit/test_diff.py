"""Diff parsing/splitting tests (SPECIFICATION §5, PRINCIPLES §8)."""

from app.diff import (
    TRUNCATION_MARKER,
    parse_changed_files,
    retriever_query,
    split_by_file,
    split_diff,
)


def test_parse_changed_files_basic(blocker_diff: str) -> None:
    assert parse_changed_files(blocker_diff) == ["app/api.py"]


def test_parse_changed_files_includes_deletions() -> None:
    diff = (
        "diff --git a/gone.py b/gone.py\n"
        "--- a/gone.py\n"
        "+++ /dev/null\n"
        "@@ -1 +0,0 @@\n-x\n"
    )
    assert parse_changed_files(diff) == ["gone.py"]


def test_parse_changed_files_plain_unified_diff() -> None:
    diff = "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-x\n+y\n"
    assert parse_changed_files(diff) == ["x.py"]


def test_parse_changed_files_without_markers() -> None:
    diff = "diff --git a/x.py b/x.py\nindex 123..456 100644\n"
    assert parse_changed_files(diff) == ["x.py"]


def test_split_by_file_keeps_blocks() -> None:
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x\n"
        "diff --git a/b.py b/b.py\n--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n-y\n"
    )
    chunks = split_by_file(diff)
    assert len(chunks) == 2
    assert "a.py" in chunks[0] and "b.py" in chunks[1]


def test_split_diff_small_untouched() -> None:
    diff = "diff --git a/a.py b/a.py\n+++ b/a.py\n"
    assert split_diff(diff, max_lines=100) == [diff]


def _file_diff(name: str, body_lines: int) -> str:
    body = "".join(f"+line {i}\n" for i in range(body_lines))
    return (
        f"diff --git a/{name} b/{name}\n--- a/{name}\n+++ b/{name}\n"
        f"@@ -1,1 +1,{body_lines} @@\n{body}"
    )


def test_split_diff_large_splits_per_file() -> None:
    diff = _file_diff("a.py", 20) + _file_diff("b.py", 20)
    chunks = split_diff(diff, max_lines=15)
    assert len(chunks) == 2
    assert all(len(c.splitlines()) <= 16 for c in chunks)


def test_split_diff_single_oversized_file_truncates() -> None:
    diff = _file_diff("big.py", 50)
    chunks = split_diff(diff, max_lines=10)
    assert len(chunks) == 1
    assert TRUNCATION_MARKER.strip() in chunks[0]
    assert len(chunks[0].splitlines()) <= 11 + 1


def test_retriever_query() -> None:
    assert retriever_query(["a.py", "b.py"], "myrepo") == "myrepo | a.py, b.py"
    assert retriever_query([], "") == "code review context"
