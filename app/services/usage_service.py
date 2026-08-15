import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.usage_log import UsageLog

logger = structlog.get_logger("myai.usage")


class UsageService:
    """Usage persistence must never break the main request - any failure
    here is logged and swallowed, per the spec's requirement that usage
    tracking not cause the primary request to fail."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def record(
        self,
        *,
        project_id: uuid.UUID | None,
        user_id: uuid.UUID | None,
        model_id: uuid.UUID | None,
        provider: str,
        input_tokens: int | None,
        output_tokens: int | None,
        latency_ms: int,
        status: str,
        request_id: str,
    ) -> None:
        try:
            self._db.add(
                UsageLog(
                    project_id=project_id,
                    user_id=user_id,
                    model_id=model_id,
                    provider=provider,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    status=status,
                    request_id=request_id,
                )
            )
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            logger.warning("usage_log_persist_failed", request_id=request_id)
