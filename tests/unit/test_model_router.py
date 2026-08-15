import pytest

from app.core.exceptions import ValidationAppError
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter


async def test_auto_routes_short_message_to_glm(db_session):
    router = ModelRouter(ModelRegistry(db_session))
    decision = await router.resolve("auto", ["What's the capital of France?"])
    assert decision.model.name == "glm-5.2"


async def test_auto_routes_long_message_to_kimi(db_session):
    router = ModelRouter(ModelRegistry(db_session))
    long_message = "explain this codebase in detail. " * 300  # exceeds the long-context threshold
    decision = await router.resolve("auto", [long_message])
    assert decision.model.name == "kimi-k3"


async def test_auto_routes_complex_keyword_to_kimi(db_session):
    router = ModelRouter(ModelRegistry(db_session))
    decision = await router.resolve("auto", ["Can you help me debug this step by step?"])
    assert decision.model.name == "kimi-k3"


async def test_explicit_model_selection_is_honored(db_session):
    router = ModelRouter(ModelRegistry(db_session))
    decision = await router.resolve("kimi-k3", ["hi"])
    assert decision.model.name == "kimi-k3"
    assert decision.reason == "explicit selection"


async def test_unknown_model_raises(db_session):
    router = ModelRouter(ModelRegistry(db_session))
    with pytest.raises(ValidationAppError):
        await router.resolve("gpt-5", ["hi"])
