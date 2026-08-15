import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Principal, get_current_principal
from app.core.exceptions import AuthorizationError
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectOut
from app.services.audit_service import AuditService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/v1/projects", tags=["projects"])


def _require_user(principal: Principal) -> None:
    if principal.kind != "user":
        raise AuthorizationError("This endpoint requires user authentication")


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    _require_user(principal)
    user = await db.get(User, principal.user_id)
    project = await ProjectService(db).create(owner=user, name=payload.name, description=payload.description)

    audit = AuditService(db)
    audit.log(action="project.created", resource_type="project", resource_id=str(project.id), user_id=user.id, project_id=project.id)
    await db.commit()

    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects(principal: Principal = Depends(get_current_principal), db: AsyncSession = Depends(get_db)):
    _require_user(principal)
    user = await db.get(User, principal.user_id)
    return await ProjectService(db).list_for_user(user)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    _require_user(principal)
    user = await db.get(User, principal.user_id)
    return await ProjectService(db).get_owned(project_id, user=user)
