"""LLM client tests (SPECIFICATION §1, §5 — temperature 0)."""

from types import SimpleNamespace

import pytest

from app.llm import LLMClient, LLMError


class FakeOpenAI:
    def __init__(self, content="ok", raises=None):
        self.raises = raises
        self.content = content
        self.kwargs = None
        outer = self

        class Completions:
            def create(self, **kwargs):
                outer.kwargs = kwargs
                if outer.raises:
                    raise outer.raises
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content=outer.content)
                        )
                    ]
                )

        self.chat = SimpleNamespace(completions=Completions())


def test_complete_sends_messages_and_temperature() -> None:
    fake = FakeOpenAI(content="hello")
    client = LLMClient("gpt-4o-mini", "sk-test", client=fake)
    out = client.complete("sys", "usr", temperature=0.0)
    assert out == "hello"
    assert fake.kwargs["model"] == "gpt-4o-mini"
    assert fake.kwargs["temperature"] == 0.0
    assert fake.kwargs["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "usr"},
    ]


def test_provider_failure_raises_llm_error() -> None:
    fake = FakeOpenAI(raises=RuntimeError("boom"))
    client = LLMClient("m", "k", client=fake)
    with pytest.raises(LLMError, match="boom"):
        client.complete("s", "u")


def test_empty_completion_raises() -> None:
    fake = FakeOpenAI(content="   ")
    client = LLMClient("m", "k", client=fake)
    with pytest.raises(LLMError, match="empty"):
        client.complete("s", "u")
