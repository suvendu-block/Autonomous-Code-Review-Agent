"""LangSmith tracing (PRINCIPLES.md §7: no node ships without a span).

One trace per review run; each graph node is a span. Tracing is enabled by
``LANGSMITH_API_KEY`` (``SPECIFICATION.md §2``). Tracing must never break a
review: every export failure degrades to a logged warning instead of an
exception.
"""

from __future__ import annotations

import sys
from typing import Any

DEFAULT_PROJECT = "code-review-agent"
ROOT_RUN_NAME = "code_review"


def _warn(message: str) -> None:
    print(f"tracing warning: {message}", file=sys.stderr)


def jsonable(value: Any) -> Any:
    """Best-effort JSON-safe conversion (pydantic models, sets, …)."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return str(value)


class Tracer:
    """Span exporter. A disabled tracer is a zero-overhead no-op."""

    def __init__(
        self,
        api_key: str | None,
        project: str = DEFAULT_PROJECT,
        *,
        client: Any = None,
        run_tree_cls: Any = None,
    ) -> None:
        self.enabled = bool(api_key)
        self.project = project
        self.trace_url: str | None = None
        self._root: Any = None
        self._spans: dict[str, Any] = {}
        self._run_tree_cls = run_tree_cls
        self._client = client
        if self.enabled and self._client is None:
            try:
                from langsmith import Client

                self._client = Client(api_key=api_key)
            except Exception as exc:
                _warn(f"disabled ({exc})")
                self.enabled = False

    def _run_tree_cls_or_import(self) -> Any:
        if self._run_tree_cls is not None:
            return self._run_tree_cls
        from langsmith.run_trees import RunTree

        return RunTree

    def _safe(self, action: str, fn) -> None:
        if not self.enabled:
            return
        try:
            fn()
        except Exception as exc:
            _warn(f"{action} failed ({exc}); tracing disabled")
            self.enabled = False

    def start_trace(self, inputs: dict[str, Any]) -> None:
        if not self.enabled:
            return

        def _start() -> None:
            cls = self._run_tree_cls_or_import()
            self._root = cls(
                name=ROOT_RUN_NAME,
                run_type="chain",
                inputs=jsonable(inputs),
                session_name=self.project,
                ls_client=self._client,
                tags=["autonomous-code-review"],
            )
            self._root.post()
            self._flush()
            # Resolve eagerly so the report node can embed trace_url.
            self._resolve_url()

        self._safe("start_trace", _start)

    def _flush(self) -> None:
        flush = getattr(self._client, "flush", None)
        if callable(flush):
            flush(timeout=15)

    def _resolve_url(self) -> None:
        """Resolve once; a URL failure must not disable tracing."""
        if self.trace_url is not None or self._root is None:
            return
        try:
            self.trace_url = self._root.get_url()
        except Exception as exc:
            _warn(f"trace url unavailable ({exc})")

    def start_span(self, name: str, inputs: dict[str, Any]) -> None:
        if not self.enabled or self._root is None:
            return

        def _start() -> None:
            self._spans[name] = self._root.create_child(
                name=name, run_type="chain", inputs=jsonable(inputs)
            )
            self._spans[name].post()

        self._safe(f"start_span({name})", _start)

    def end_span(
        self,
        name: str,
        outputs: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        if not self.enabled or name not in self._spans:
            return
        span = self._spans.pop(name)

        def _end() -> None:
            span.end(outputs=jsonable(outputs) if outputs is not None else None,
                     error=error)
            span.patch()

        self._safe(f"end_span({name})", _end)

    def finish_trace(self, outputs: dict[str, Any]) -> None:
        if not self.enabled or self._root is None:
            return

        def _finish() -> None:
            self._root.end(outputs=jsonable(outputs))
            self._root.patch()
            self._flush()
            self._resolve_url()

        self._safe("finish_trace", _finish)
