import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Principal, get_current_principal, require_project_access
from app.db.session import get_db
from app.schemas.api_key import APIKeyCreate, APIKeyCreated, APIKeyOut
from app.services.api_key_service import APIKeyService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/v1/projects/{project_id}/api-keys", tags=["api-keys"])


@router.post("", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    project_id: uuid.UUID,
    payload: APIKeyCreate,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    await require_project_access(project_id, principal, db)
    api_key, full_key = await APIKeyService(db).create(
        project_id=project_id, name=payload.name, scopes=payload.scopes, expires_in_days=payload.expires_in_days
    )

    audit = AuditService(db)
    audit.log(
        action="api_key.created", resource_type="api_key", resource_id=str(api_key.id),
        user_id=principal.user_id, project_id=project_id, metadata={"name": payload.name},
    )
    await db.commit()

    # `full_key` is returned here and ONLY here - it is never stored or logged.
    return APIKeyCreated(
        id=api_key.id, name=api_key.name, key=full_key, key_prefix=api_key.key_prefix,
        scopes=api_key.scopes, expires_at=api_key.expires_at,
    )


@router.get("", response_model=list[APIKeyOut])
async def list_api_keys(
    project_id: uuid.UUID,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    await require_project_access(project_id, principal, db)
    return await APIKeyService(db).list_for_project(project_id)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    project_id: uuid.UUID,
    key_id: uuid.UUID,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    await require_project_access(project_id, principal, db)
    await APIKeyService(db).revoke(key_id, project_id=project_id)

    audit = AuditService(db)
    audit.log(
        action="api_key.revoked", resource_type="api_key", resource_id=str(key_id),
        user_id=principal.user_id, project_id=project_id,
    )
    await db.commit()
