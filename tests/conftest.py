"""Shared pytest fixtures: settings, fake LLM, graph contexts, diffs."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.nodes import GraphContext
from app.tracing import Tracer

BASE_ENV = {
    "LLM_MODEL": "gpt-4o-mini",
    "LLM_API_KEY": "sk-test",
    "LANGSMITH_API_KEY": "",
    "LANGSMITH_PROJECT": "code-review-agent",
    "CHROMA_PATH": "./.chroma",
    "EMBEDDING_MODEL": "text-embedding-3-small",
    "MAX_DIFF_LINES": "3000",
    "REVIEW_SEVERITY": "normal",
}

BLOCKER_DIFF = """\
diff --git a/app/api.py b/app/api.py
--- a/app/api.py
+++ b/app/api.py
@@ -1,4 +1,5 @@
 def get_user(cursor, user_id):
+    query = "SELECT * FROM users WHERE id = " + user_id
-    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
+    cursor.execute(query)
     return cursor.fetchone()
"""

CLEAN_DIFF = '''\
diff --git a/app/utils.py b/app/utils.py
--- a/app/utils.py
+++ b/app/utils.py
@@ -1,3 +1,4 @@
+"""Helpers."""
 def clamp(value, low, high):
     return max(low, min(high, value))
'''

DOCS_DIFF = """\
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Project
+Docs update.
"""


class FakeLLM:
    """Scripted LLM. Records every call incl. temperature."""

    def __init__(self, responses=None, default="[]", error=None):
        self.responses = list(responses or [])
        self.default = default
        self.error = error
        self.calls: list[dict] = []

    def complete(self, system, user, *, temperature=0.0):
        self.calls.append(
            {"system": system, "user": user, "temperature": temperature}
        )
        if self.error is not None:
            raise self.error if isinstance(self.error, Exception) else RuntimeError(self.error)
        if self.responses:
            response = self.responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return self.default

    @property
    def temperatures(self) -> list[float]:
        return [call["temperature"] for call in self.calls]


def make_settings(monkeypatch: pytest.MonkeyPatch, **overrides) -> Settings:
    for key, value in {**BASE_ENV, **overrides}.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)


@pytest.fixture
def settings_factory(monkeypatch):
    return lambda **overrides: make_settings(monkeypatch, **overrides)


@pytest.fixture
def settings(settings_factory) -> Settings:
    return settings_factory()


@pytest.fixture
def make_llm():
    return FakeLLM


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def make_ctx(settings):
    def _make(
        llm=None,
        *,
        settings_override: Settings | None = None,
        retriever=None,
        output_path: str | None = None,
        tracer: Tracer | None = None,
    ) -> GraphContext:
        return GraphContext(
            settings=settings_override or settings,
            llm=llm or FakeLLM(),
            tracer=tracer or Tracer(None),
            retriever=retriever,
            output_path=output_path,
        )

    return _make


@pytest.fixture
def blocker_diff() -> str:
    return BLOCKER_DIFF


@pytest.fixture
def clean_diff() -> str:
    return CLEAN_DIFF


@pytest.fixture
def docs_diff() -> str:
    return DOCS_DIFF
