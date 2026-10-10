"""Unified-diff parsing and bounded splitting.

SPECIFICATION.md §5 (diff larger than MAX_DIFF_LINES is split per file),
PRINCIPLES.md §8 (bounded work, truncation guard).
"""

from __future__ import annotations

TRUNCATION_MARKER = "\n... (truncated: diff exceeds MAX_DIFF_LINES)\n"

GIT_HEADER_PREFIX = "diff --git "
PLUS_PLUS_PREFIX = "+++ "


def parse_changed_files(diff: str) -> list[str]:
    """Return changed file paths from a unified diff, in order of appearance."""
    files: list[str] = []

    def _add(path: str) -> None:
        path = path.strip()
        if path and path not in files:
            files.append(path)

    # Preferred: git summary lines (also covers deletions, renames).
    for line in diff.splitlines():
        if line.startswith(GIT_HEADER_PREFIX):
            parts = line[len(GIT_HEADER_PREFIX):].split()
            if len(parts) == 2:
                target = parts[1]
                _add(target[2:] if target.startswith("b/") else target)
    if files:
        return files

    # Fallback: plain unified diff markers.
    for line in diff.splitlines():
        if line.startswith(PLUS_PLUS_PREFIX):
            path = line[len(PLUS_PLUS_PREFIX):].strip()
            if path == "/dev/null":
                continue
            if path.startswith("b/"):
                path = path[2:]
            _add(path)
    return files


def split_by_file(diff: str) -> list[str]:
    """Split a diff into one chunk per file block."""
    chunks: list[str] = []
    current: list[str] = []
    for line in diff.splitlines(keepends=True):
        if line.startswith(GIT_HEADER_PREFIX) and current:
            chunks.append("".join(current))
            current = []
        current.append(line)
    if current:
        chunks.append("".join(current))
    return chunks


def _truncate(chunk: str, max_lines: int) -> str:
    lines = chunk.splitlines()
    if len(lines) <= max_lines:
        return chunk
    return "\n".join(lines[:max_lines]) + TRUNCATION_MARKER


def split_diff(diff: str, max_lines: int) -> list[str]:
    """Split ``diff`` into reviewable chunks of at most ``max_lines`` lines.

    Small diffs come back untouched as a single chunk. Large diffs are split
    per file; a single oversized file is truncated with an explicit marker.
    """
    total = len(diff.splitlines())
    if total <= max_lines:
        return [diff]
    chunks = split_by_file(diff)
    if len(chunks) <= 1:
        return [_truncate(chunks[0], max_lines)]
    return [_truncate(chunk, max_lines) for chunk in chunks]


def retriever_query(files: list[str], repo: str = "") -> str:
    """Build the context-retrieval query from the diff (SPECIFICATION §4)."""
    parts = [p for p in (repo.strip(), ", ".join(files)) if p]
    return " | ".join(parts) if parts else "code review context"
