import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.security import generate_api_key
from app.db.models.api_key import APIKey


class APIKeyService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self, *, project_id: uuid.UUID, name: str, scopes: list[str], expires_in_days: int | None
    ) -> tuple[APIKey, str]:
        full_key, prefix, key_hash = generate_api_key()
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days) if expires_in_days else None

        api_key = APIKey(
            project_id=project_id, name=name, key_prefix=prefix, key_hash=key_hash, scopes=scopes,
            expires_at=expires_at,
        )
        self._db.add(api_key)
        await self._db.commit()
        await self._db.refresh(api_key)
        return api_key, full_key

    async def list_for_project(self, project_id: uuid.UUID) -> list[APIKey]:
        result = await self._db.execute(select(APIKey).where(APIKey.project_id == project_id))
        return list(result.scalars().all())

    async def revoke(self, api_key_id: uuid.UUID, *, project_id: uuid.UUID) -> None:
        api_key = await self._db.get(APIKey, api_key_id)
        if not api_key or api_key.project_id != project_id:
            raise NotFoundError("API key not found")
        api_key.revoked_at = datetime.now(timezone.utc)
        await self._db.commit()
