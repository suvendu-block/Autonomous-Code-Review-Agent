"""LLM access layer (SPECIFICATION.md §1 — pluggable provider, temperature 0)."""

from __future__ import annotations

from typing import Protocol

from app.config import Settings


class LLMError(Exception):
    """Raised when the model cannot produce a usable completion."""


class LLM(Protocol):
    """What nodes see: a single blocking completion call."""

    def complete(
        self, system: str, user: str, *, temperature: float = 0.0
    ) -> str: ...


class LLMClient:
    """OpenAI-compatible chat completions client.

    ``OPENAI_BASE_URL`` (standard SDK env var) routes to any
    OpenAI-compatible provider without config changes.
    """

    def __init__(self, model: str, api_key: str, *, client=None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self._client = client
        self.model = model

    def complete(
        self, system: str, user: str, *, temperature: float = 0.0
    ) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
            )
            content = response.choices[0].message.content
        except Exception as exc:  # provider/network/auth failures
            raise LLMError(str(exc)) from exc
        if not content or not content.strip():
            raise LLMError("empty completion")
        return content


def build_llm(settings: Settings) -> LLMClient:
    return LLMClient(settings.llm_model, settings.llm_api_key)
