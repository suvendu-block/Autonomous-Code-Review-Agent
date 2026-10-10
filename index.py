"""Entry point: config skeleton plus the ``review`` CLI (STEPS.md §1, T-003).

    python index.py                     # config + node list
    python index.py review <diff|->     # run an autonomous review
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.config import ConfigError, load_settings
from app.nodes import NODE_ORDER


def _ensure_utf8_output() -> None:
    """Reports contain emoji (SPECIFICATION §6) — never crash the CLI."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_output()
    argv = list(argv) if argv else []
    if argv:
        command, rest = argv[0], argv[1:]
        if command == "review":
            return review_command(rest)
        if command in ("-h", "--help", "help"):
            _print_usage()
            return 0
        print(f"unknown command: {command}", file=sys.stderr)
        return 2
    return skeleton()


def _print_usage() -> None:
    print(
        "usage: index.py [review <diff|->]\n"
        "\n"
        "commands:\n"
        "  (none)             load config, print model + node list\n"
        "  review <diff|->    run an autonomous review over a unified diff\n"
        "                     ('-' reads from stdin; -o sets the JSON\n"
        "                     artifact path, default review_report.json)\n"
        "  --help             show this message\n"
        "\n"
        "exit codes: 0 clean · 1 blocker/major findings · 2 failure"
    )


def skeleton() -> int:
    """Load config and print model + node list (STEPS.md §1)."""
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    print(f"model: {settings.llm_model}")
    print(f"severity: {settings.review_severity}")
    print(f"max_diff_lines: {settings.max_diff_lines}")
    print(f"tracing: {'on' if settings.langsmith_api_key else 'off'}")
    print(f"nodes ({len(NODE_ORDER)}):")
    for position, node in enumerate(NODE_ORDER, start=1):
        print(f"  {position}. {node}")
    return 0


def review_command(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="index.py review",
        description="Run an autonomous review over a unified diff.",
    )
    parser.add_argument(
        "diff", help="path to a unified diff file, or '-' for stdin"
    )
    parser.add_argument(
        "-o", "--output", default="review_report.json",
        help="JSON artifact path (default: review_report.json)",
    )
    parser.add_argument("--repo", default="", help="repository label")
    parser.add_argument(
        "--no-record", action="store_true",
        help="do not append findings to the past_reviews collection",
    )
    args = parser.parse_args(argv)

    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    if args.diff == "-":
        diff = sys.stdin.read()
    else:
        path = Path(args.diff)
        try:
            diff = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"diff read error: {exc}", file=sys.stderr)
            return 2
    if not diff.strip():
        print("diff error: diff is empty", file=sys.stderr)
        return 2

    from app import memory  # local import: keeps skeleton startup light
    from app.runner import ReviewError, run_review

    retriever = None
    if Path(settings.chroma_path).exists():
        def retriever(query: str) -> list[str]:
            return memory.retrieve(settings, query)

    try:
        result = run_review(
            diff,
            settings,
            retriever=retriever,
            output_path=args.output,
            record=not args.no_record,
            repo=args.repo,
        )
    except ReviewError as exc:
        print(f"review failed: {exc}", file=sys.stderr)
        return 2

    print(result.markdown)
    for error in result.state.get("errors", []):
        print(f"node error: {error}", file=sys.stderr)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
