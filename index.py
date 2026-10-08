"""Entry point: loads config, prints model + node list (STEPS.md §1)."""

from __future__ import annotations

import sys

from app.config import ConfigError, load_settings
from app.nodes import NODE_ORDER


def main() -> int:
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


if __name__ == "__main__":
    sys.exit(main())
