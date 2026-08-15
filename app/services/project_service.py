import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.user import User


class ProjectService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, *, owner: User, name: str, description: str | None) -> Project:
        organization_id = owner.organization_id
        if organization_id is None:
            # V1 has no organization-management UI, so every user gets an
            # implicit personal organization the first time they create a project.
            org = Organization(name=f"{owner.email}'s workspace", slug=f"org-{owner.id.hex[:12]}")
            self._db.add(org)
            await self._db.flush()
            owner.organization_id = org.id
            organization_id = org.id

        project = Project(name=name, description=description, organization_id=organization_id, owner_id=owner.id)
        self._db.add(project)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def list_for_user(self, user: User) -> list[Project]:
        result = await self._db.execute(select(Project).where(Project.owner_id == user.id))
        return list(result.scalars().all())

    async def get_owned(self, project_id: uuid.UUID, *, user: User) -> Project:
        project = await self._db.get(Project, project_id)
        if not project or project.owner_id != user.id:
            raise NotFoundError("Project not found")
        return project
