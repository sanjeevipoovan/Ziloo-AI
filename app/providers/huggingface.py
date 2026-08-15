"""
Hugging Face provider implementation.

This is the ONLY module in the application that imports huggingface_hub.
Everything else talks to LLMProvider. `model_identifier` and credentials
are passed in from configuration (via the Model Registry / Settings) -
this class has no idea what "GLM-5.2" or "Kimi K3" are conceptually, only
whatever repo id and token it's given at call time.

Uses AsyncInferenceClient.chat_completion(), which follows the OpenAI
chat-completions request/response shape (see huggingface_hub's inference
guide), so response parsing here mirrors what you'd do against an OpenAI
`/v1/chat/completions` payload.
"""
import asyncio
from collections.abc import AsyncIterator

from huggingface_hub import AsyncInferenceClient
from huggingface_hub.errors import HfHubHTTPError

from app.core.config import get_settings
from app.providers.base import LLMProvider, ProviderMessage, ProviderResponse, ProviderStreamChunk, ProviderUsage
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

settings = get_settings()


class HuggingFaceProvider(LLMProvider):
    name = "huggingface"

    def __init__(self, token: str | None = None, timeout: float | None = None):
        self._client = AsyncInferenceClient(
            token=token or settings.HF_API_TOKEN,
            timeout=timeout or settings.PROVIDER_TIMEOUT_SECONDS,
        )

    @staticmethod
    def _to_hf_messages(messages: list[ProviderMessage]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def generate(
        self,
        *,
        model_identifier: str,
        messages: list[ProviderMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ProviderResponse:
        try:
            completion = await self._client.chat_completion(
                messages=self._to_hf_messages(messages),
                model=model_identifier,
                # HF/TGI reject temperature=0; clamp to a tiny positive value
                # so callers can still request "deterministic" generation.
                temperature=max(temperature, 0.01),
                max_tokens=max_tokens,
                stream=False,
            )
        except TimeoutError as exc:
            raise ProviderTimeoutError(str(exc)) from exc
        except HfHubHTTPError as exc:
            raise self._translate_http_error(exc) from exc
        except Exception as exc:  # noqa: BLE001 - isolate every vendor error at this boundary
            raise ProviderResponseError(str(exc)) from exc

        choice = completion.choices[0]
        usage = completion.usage
        return ProviderResponse(
            content=choice.message.content or "",
            model=completion.model or model_identifier,
            finish_reason=choice.finish_reason,
            usage=ProviderUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            ),
            raw={"id": getattr(completion, "id", None)},
        )

    async def stream(
        self,
        *,
        model_identifier: str,
        messages: list[ProviderMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        try:
            hf_stream = await self._client.chat_completion(
                messages=self._to_hf_messages(messages),
                model=model_identifier,
                temperature=max(temperature, 0.01),
                max_tokens=max_tokens,
                stream=True,
            )
            async for event in hf_stream:
                choice = event.choices[0]
                delta = choice.delta.content or ""
                finish_reason = choice.finish_reason
                usage = None
                event_usage = getattr(event, "usage", None)
                if finish_reason and event_usage:
                    usage = ProviderUsage(
                        prompt_tokens=getattr(event_usage, "prompt_tokens", 0) or 0,
                        completion_tokens=getattr(event_usage, "completion_tokens", 0) or 0,
                    )
                yield ProviderStreamChunk(delta=delta, finish_reason=finish_reason, usage=usage)
        except TimeoutError as exc:
            raise ProviderTimeoutError(str(exc)) from exc
        except HfHubHTTPError as exc:
            raise self._translate_http_error(exc) from exc
        except (ProviderTimeoutError, ProviderUnavailableError, ProviderAuthenticationError, ProviderResponseError):
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderResponseError(str(exc)) from exc

    async def health_check(self, *, model_identifier: str) -> bool:
        try:
            await self._client.chat_completion(
                messages=[{"role": "user", "content": "ping"}],
                model=model_identifier,
                max_tokens=1,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def _translate_http_error(exc: HfHubHTTPError) -> Exception:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if status_code in (401, 403):
            return ProviderAuthenticationError(str(exc))
        if status_code in (503, 504):
            return ProviderUnavailableError(str(exc))
        return ProviderResponseError(str(exc))
