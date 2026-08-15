import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog


class AuditService:
    """Lightweight audit trail for security-sensitive actions (API key
    lifecycle, project creation, ...). Caller commits as part of its own
    transaction - this only stages the row."""

    def __init__(self, db: AsyncSession):
        self._db = db

    def log(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None,
        user_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> None:
        self._db.add(
            AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                project_id=project_id,
                metadata_=metadata or {},
            )
        )
