"""Test doubles for LLMProvider, injected via Orchestrator(db, provider=...)
so provider behavior can be controlled per-test without monkeypatching."""
from collections.abc import AsyncIterator

from app.providers.base import LLMProvider, ProviderResponse, ProviderStreamChunk, ProviderUsage
from app.providers.exceptions import ProviderUnavailableError


class FakeProvider(LLMProvider):
    name = "fake"

    async def generate(self, *, model_identifier, messages, temperature=0.7, max_tokens=None) -> ProviderResponse:
        return ProviderResponse(
            content=f"fake response for {model_identifier}",
            model=model_identifier,
            finish_reason="stop",
            usage=ProviderUsage(prompt_tokens=10, completion_tokens=5),
        )

    async def stream(self, *, model_identifier, messages, temperature=0.7, max_tokens=None) -> AsyncIterator[ProviderStreamChunk]:
        for word in ("Hello", " ", "world"):
            yield ProviderStreamChunk(delta=word)
        yield ProviderStreamChunk(delta="", finish_reason="stop", usage=ProviderUsage(prompt_tokens=10, completion_tokens=3))

    async def health_check(self, *, model_identifier) -> bool:
        return True


class FailingProvider(LLMProvider):
    name = "failing"

    async def generate(self, *, model_identifier, messages, temperature=0.7, max_tokens=None) -> ProviderResponse:
        raise ProviderUnavailableError("simulated provider outage")

    async def stream(self, *, model_identifier, messages, temperature=0.7, max_tokens=None) -> AsyncIterator[ProviderStreamChunk]:
        raise ProviderUnavailableError("simulated provider outage")
        yield  # pragma: no cover - unreachable; makes this an async generator

    async def health_check(self, *, model_identifier) -> bool:
        return False
