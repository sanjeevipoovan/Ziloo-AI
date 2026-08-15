"""
Model Registry: looks up registered (Provider, AIModel) rows from the
database. This is one of the two primary extension points named in the
spec (the other is the LLMProvider interface) - adding a model means
inserting a row (see app/db/seed.py), not touching application code.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.model import AIModel
from app.db.models.provider import Provider


class ModelRegistry:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_name(self, name: str) -> AIModel | None:
        result = await self._db.execute(select(AIModel).where(AIModel.name == name, AIModel.is_active.is_(True)))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[AIModel]:
        result = await self._db.execute(select(AIModel).where(AIModel.is_active.is_(True)))
        return list(result.scalars().all())

    async def get_provider(self, provider_id: uuid.UUID) -> Provider | None:
        return await self._db.get(Provider, provider_id)
