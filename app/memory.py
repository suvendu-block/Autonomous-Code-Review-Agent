"""ChromaDB memory layer (ARCHITECTURE.md — Memory layer).

Three collections: ``project_conventions``, ``past_reviews``,
``codebase_docs``. Retrieval returns at most 8 chunks
(SPECIFICATION.md §4); errors bubble up to the ``context_retriever`` node,
which degrades to empty context.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Protocol

from app.config import Settings
from app.models import ReviewReport

CONVENTIONS = "project_conventions"
PAST_REVIEWS = "past_reviews"
DOCS = "codebase_docs"
COLLECTIONS = (CONVENTIONS, DOCS, PAST_REVIEWS)

MAX_CONTEXT_CHUNKS = 8
_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 100
_DOC_SUFFIXES = {".md", ".rst", ".txt"}
_DOC_STEMS = {"readme", "changelog", "license", "authors", "history"}
_CONVENTION_FILES = {
    "contributing",
    "code_of_conduct",
    "code-of-conduct",
    ".editorconfig",
    ".pre-commit-config.yaml",
    "pyproject.toml",
    "setup.cfg",
    "ruff.toml",
}
# Quota per collection so one noisy source cannot starve the others.
_QUOTAS = ((DOCS, 3), (CONVENTIONS, 3), (PAST_REVIEWS, 2))
_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".chroma", "dist", "build"}


class Embedder(Protocol):
    def __call__(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbedder:
    """Embeddings via the OpenAI-compatible API (``EMBEDDING_MODEL``)."""

    def __init__(self, model: str, api_key: str, *, client: Any = None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self._client = client
        self.model = model

    def __call__(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


def _chroma_ef(embedder: Embedder):
    """Wrap our embedder in a Chroma embedding function."""

    class _EF:
        def __call__(self, input):  # noqa: A002 - chroma protocol
            return embedder(list(input))

        def embed_query(self, input):  # noqa: A002 - chroma protocol
            return self(input)

        def name(self) -> str:
            return "app_embedder"

        def is_legacy(self) -> bool:
            # Explicitly legacy: the EF is always supplied by our code on
            # open (never rebuilt from persisted config), so no registration
            # in chromadb's registry is required.
            return True

    return _EF()


def _build_embedder(settings: Settings, embedder: Embedder | None) -> Embedder:
    if embedder is not None:
        return embedder
    return OpenAIEmbedder(settings.embedding_model, settings.llm_api_key)


def get_client(settings: Settings):
    import chromadb

    return chromadb.PersistentClient(path=settings.chroma_path)


def get_collections(
    settings: Settings,
    embedder: Embedder | None = None,
    *,
    client: Any = None,
    reset: bool = False,
):
    ef = _chroma_ef(_build_embedder(settings, embedder))
    client = client or get_client(settings)
    if reset:
        for name in COLLECTIONS:
            try:
                client.delete_collection(name)
            except Exception:
                pass  # not created yet
    return {
        name: client.get_or_create_collection(name, embedding_function=ef)
        for name in COLLECTIONS
    }


def chunk_text(
    text: str, size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP
) -> list[str]:
    """Split text into overlapping chunks on line boundaries."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in text.splitlines():
        if current and current_len + len(line) + 1 > size:
            chunks.append("\n".join(current))
            keep: list[str] = []
            kept_len = 0
            for prev in reversed(current):
                if kept_len + len(prev) + 1 > overlap:
                    break
                keep.insert(0, prev)
                kept_len += len(prev) + 1
            current = keep
            current_len = kept_len
        current.append(line)
        current_len += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return [c for c in chunks if c.strip()]


def _classify(path: Path) -> str | None:
    name = path.name.lower()
    if name.startswith("review_report") and name.endswith(".json"):
        return PAST_REVIEWS
    if name in _CONVENTION_FILES or name.startswith("contributing"):
        return CONVENTIONS
    if path.suffix.lower() == ".md":
        return DOCS
    if path.suffix.lower() in _DOC_SUFFIXES and path.stem.lower() in _DOC_STEMS:
        return DOCS
    return None


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in _SKIP_DIRS for part in path.parts):
            continue
        yield path


def ingest_repo(
    repo_path: str | Path,
    settings: Settings,
    *,
    embedder: Embedder | None = None,
    reset: bool = False,
) -> dict[str, int]:
    """Embed repository docs/conventions/reviews into the three collections."""
    root = Path(repo_path).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")
    client = get_client(settings)
    collections = get_collections(settings, embedder, client=client, reset=reset)

    counts = {name: 0 for name in COLLECTIONS}
    for path in _iter_files(root):
        bucket = _classify(path)
        if bucket is None:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not text.strip():
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        chunks = chunk_text(text)
        if not chunks:
            continue
        ids = [
            hashlib.sha1(f"{rel}:{i}".encode()).hexdigest()
            for i in range(len(chunks))
        ]
        metadatas = [{"source": rel, "chunk": i} for i in range(len(chunks))]
        collections[bucket].upsert(
            ids=ids, documents=chunks, metadatas=metadatas
        )
        counts[bucket] += len(chunks)
    return counts


def retrieve(
    settings: Settings,
    query: str,
    *,
    embedder: Embedder | None = None,
    k: int = MAX_CONTEXT_CHUNKS,
) -> list[str]:
    """Fetch up to ``k`` chunks across all collections (SPECIFICATION §4)."""
    collections = get_collections(settings, embedder)
    results: list[str] = []
    seen: set[str] = set()
    for name, quota in _QUOTAS:
        if len(results) >= k:
            break
        collection = collections[name]
        if collection.count() == 0:
            continue
        n = min(quota, k - len(results))
        found = collection.query(query_texts=[query], n_results=n)
        for group in found.get("documents") or []:
            for doc in group:
                if doc and doc not in seen and len(results) < k:
                    seen.add(doc)
                    results.append(doc)
    return results


def record_review(
    settings: Settings,
    report: ReviewReport,
    *,
    embedder: Embedder | None = None,
) -> int:
    """Append a finished report's findings to ``past_reviews`` (best effort)."""
    if not report.findings:
        return 0
    collections = get_collections(settings, embedder)
    collection = collections[PAST_REVIEWS]
    documents = [
        f"{f.file}:{f.line} [{f.severity}/{f.category}] {f.title} — {f.detail}"
        for f in report.findings
    ]
    run_id = hashlib.sha1(report.model_dump_json().encode()).hexdigest()
    ids = [f"{run_id}:{i}" for i in range(len(documents))]
    metadatas = [
        {"source": f.file, "severity": f.severity, "category": f.category}
        for f in report.findings
    ]
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(documents)
