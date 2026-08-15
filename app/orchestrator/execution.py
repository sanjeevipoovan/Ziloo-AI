"""
Execution Engine: runs a single call against a provider and, for
streaming, emits only safe, high-level lifecycle events - never raw
provider payloads or internal reasoning. Also the boundary where
provider-specific exceptions become generic MyAIException subclasses, so
nothing above this layer needs to know Hugging Face exists.
"""
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.core.exceptions import ModelUnavailableError, ProviderError
from app.providers.base import LLMProvider, ProviderMessage, ProviderResponse
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


@dataclass
class ExecutionResult:
    response: ProviderResponse
    latency_ms: int


class ExecutionEngine:
    def __init__(self, provider: LLMProvider):
        self._provider = provider

    async def run(
        self,
        *,
        model_identifier: str,
        messages: list[ProviderMessage],
        temperature: float,
        max_tokens: int | None,
    ) -> ExecutionResult:
        start = time.monotonic()
        try:
            response = await self._provider.generate(
                model_identifier=model_identifier, messages=messages, temperature=temperature, max_tokens=max_tokens
            )
        except (ProviderUnavailableError, ProviderTimeoutError) as exc:
            raise ModelUnavailableError(str(exc)) from exc
        except (ProviderAuthenticationError, ProviderResponseError) as exc:
            raise ProviderError(str(exc)) from exc

        return ExecutionResult(response=response, latency_ms=int((time.monotonic() - start) * 1000))

    async def run_stream(
        self,
        *,
        model_identifier: str,
        messages: list[ProviderMessage],
        temperature: float,
        max_tokens: int | None,
    ) -> AsyncIterator[dict]:
        try:
            async for chunk in self._provider.stream(
                model_identifier=model_identifier, messages=messages, temperature=temperature, max_tokens=max_tokens
            ):
                if chunk.delta:
                    yield {"type": "delta", "content": chunk.delta}
                if chunk.finish_reason:
                    yield {
                        "type": "response_completed",
                        "finish_reason": chunk.finish_reason,
                        "usage": {
                            "prompt_tokens": chunk.usage.prompt_tokens if chunk.usage else None,
                            "completion_tokens": chunk.usage.completion_tokens if chunk.usage else None,
                        }
                        if chunk.usage
                        else None,
                    }
        except (ProviderUnavailableError, ProviderTimeoutError) as exc:
            raise ModelUnavailableError(str(exc)) from exc
        except (ProviderAuthenticationError, ProviderResponseError) as exc:
            raise ProviderError(str(exc)) from exc
