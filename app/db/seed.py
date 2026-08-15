"""
Idempotently ensures the 'huggingface' provider and the two configured
models (glm-5.2, kimi-k3) exist in the Model Registry tables.

This is the ONE place that turns config into registry rows. Model
identifiers always come from `settings.GLM_MODEL_ID` / `settings.KIMI_MODEL_ID`
- this function never hard-codes a Hugging Face repo id. Run automatically
on startup (see app/main.py's lifespan) and safe to run repeatedly.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.model import AIModel
from app.db.models.provider import Provider

settings = get_settings()

GLM_NAME = "glm-5.2"
KIMI_NAME = "kimi-k3"

_GLM_CAPABILITIES = ["general", "coding", "summarization", "classification", "extraction"]
_KIMI_CAPABILITIES = ["reasoning", "long_context", "complex_coding", "planning"]

# Context windows are operator-adjustable defaults, not a claim about any
# specific model's real specs - update via a migration + this file if your
# configured models differ.
_GLM_CONTEXT_WINDOW = 128_000
_KIMI_CONTEXT_WINDOW = 256_000


async def seed_defaults(session: AsyncSession) -> None:
    provider = await _get_or_create_provider(session, name="huggingface", display_name="Hugging Face")

    await _get_or_create_model(
        session,
        name=GLM_NAME,
        provider_id=provider.id,
        model_identifier=settings.GLM_MODEL_ID,
        capabilities=_GLM_CAPABILITIES,
        context_window=_GLM_CONTEXT_WINDOW,
    )
    await _get_or_create_model(
        session,
        name=KIMI_NAME,
        provider_id=provider.id,
        model_identifier=settings.KIMI_MODEL_ID,
        capabilities=_KIMI_CAPABILITIES,
        context_window=_KIMI_CONTEXT_WINDOW,
    )
    await session.commit()


async def _get_or_create_provider(session: AsyncSession, *, name: str, display_name: str) -> Provider:
    result = await session.execute(select(Provider).where(Provider.name == name))
    provider = result.scalar_one_or_none()
    if provider:
        return provider
    provider = Provider(name=name, display_name=display_name)
    session.add(provider)
    await session.flush()
    return provider


async def _get_or_create_model(
    session: AsyncSession,
    *,
    name: str,
    provider_id,
    model_identifier: str,
    capabilities: list[str],
    context_window: int,
) -> AIModel:
    result = await session.execute(select(AIModel).where(AIModel.name == name))
    model = result.scalar_one_or_none()
    if model:
        # Keep the registry in sync if the operator changed the env var
        # (e.g. pointed GLM_MODEL_ID at a new HF repo) without a code change.
        model.model_identifier = model_identifier
        model.capabilities = capabilities
        return model
    model = AIModel(
        name=name,
        provider_id=provider_id,
        model_identifier=model_identifier,
        model_type="chat",
        context_window=context_window,
        capabilities=capabilities,
        is_active=True,
    )
    session.add(model)
    await session.flush()
    return model
