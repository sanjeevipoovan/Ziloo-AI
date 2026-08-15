from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.providers.base import ProviderMessage
from app.providers.huggingface import HuggingFaceProvider


def _fake_completion(content="hello there", finish_reason="stop", prompt_tokens=12, completion_tokens=4):
    return SimpleNamespace(
        id="cmpl_abc123",
        model="test-org/glm-test",
        choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish_reason)],
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
    )


async def test_generate_normalizes_response():
    with patch("app.providers.huggingface.AsyncInferenceClient") as mock_client_cls:
        mock_client_cls.return_value.chat_completion = AsyncMock(return_value=_fake_completion())

        provider = HuggingFaceProvider(token="hf_test")
        result = await provider.generate(
            model_identifier="test-org/glm-test", messages=[ProviderMessage(role="user", content="hi")]
        )

    assert result.content == "hello there"
    assert result.finish_reason == "stop"
    assert result.usage.prompt_tokens == 12
    assert result.usage.completion_tokens == 4
    assert result.usage.total_tokens == 16


async def test_generate_clamps_zero_temperature():
    with patch("app.providers.huggingface.AsyncInferenceClient") as mock_client_cls:
        mock_chat_completion = AsyncMock(return_value=_fake_completion())
        mock_client_cls.return_value.chat_completion = mock_chat_completion

        provider = HuggingFaceProvider(token="hf_test")
        await provider.generate(
            model_identifier="test-org/glm-test",
            messages=[ProviderMessage(role="user", content="hi")],
            temperature=0.0,
        )

    _, kwargs = mock_chat_completion.call_args
    assert kwargs["temperature"] > 0  # TGI/HF reject temperature=0


async def test_stream_yields_deltas_then_finish():
    async def fake_stream():
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hel"), finish_reason=None)])
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="lo"), finish_reason=None)])
        yield SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=""), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=2),
        )

    with patch("app.providers.huggingface.AsyncInferenceClient") as mock_client_cls:
        mock_client_cls.return_value.chat_completion = AsyncMock(return_value=fake_stream())

        provider = HuggingFaceProvider(token="hf_test")
        chunks = [
            chunk
            async for chunk in provider.stream(
                model_identifier="test-org/glm-test", messages=[ProviderMessage(role="user", content="hi")]
            )
        ]

    deltas = "".join(c.delta for c in chunks)
    assert deltas == "Hello"
    assert chunks[-1].finish_reason == "stop"
    assert chunks[-1].usage.prompt_tokens == 5
