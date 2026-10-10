"""Repository ingestion entry point (STEPS.md §4).

    python -m app.ingest ./repo     # creates project_conventions,
                                    # past_reviews, codebase_docs
"""

from __future__ import annotations

import argparse
import sys

from app.config import ConfigError, load_settings
from app.memory import ingest_repo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.ingest",
        description="Embed repository docs/conventions into ChromaDB.",
    )
    parser.add_argument("path", nargs="?", default=".", help="repository root")
    parser.add_argument(
        "--reset", action="store_true", help="drop existing collections first"
    )
    args = parser.parse_args(argv)

    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    try:
        counts = ingest_repo(args.path, settings, reset=args.reset)
    except NotADirectoryError as exc:
        print(f"ingest error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ingest error: {exc}", file=sys.stderr)
        return 2

    total = sum(counts.values())
    for name, count in sorted(counts.items()):
        print(f"{name}: {count} chunk(s)")
    print(f"total: {total} chunk(s) -> {settings.chroma_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
