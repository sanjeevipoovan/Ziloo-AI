"""
The provider abstraction.

Provider Abstraction -> Model Registry -> Model Router -> Provider implementation

Nothing outside app/providers/ (the router, the orchestrator, the API
routes) knows anything about Hugging Face specifically. They depend only
on LLMProvider. Adding vLLM, OpenAI, Anthropic, or a future self-hosted
MyAI model later means writing one new class here that implements this
interface - no changes to routing or orchestration logic.
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass
class ProviderMessage:
    role: str
    content: str


@dataclass
class ProviderUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class ProviderResponse:
    content: str
    model: str
    finish_reason: str | None
    usage: ProviderUsage
    raw: dict = field(default_factory=dict)


@dataclass
class ProviderStreamChunk:
    delta: str
    finish_reason: str | None = None
    usage: ProviderUsage | None = None


class LLMProvider(ABC):
    """Every model provider implements this. `model_identifier` is always
    passed in by the caller (resolved from the Model Registry) - a provider
    class never hard-codes which models it serves."""

    name: str

    @abstractmethod
    async def generate(
        self,
        *,
        model_identifier: str,
        messages: list[ProviderMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ProviderResponse: ...

    @abstractmethod
    def stream(
        self,
        *,
        model_identifier: str,
        messages: list[ProviderMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]: ...

    @abstractmethod
    async def health_check(self, *, model_identifier: str) -> bool: ...
