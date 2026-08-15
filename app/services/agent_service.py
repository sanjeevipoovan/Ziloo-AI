import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, *, project_id: uuid.UUID, data: AgentCreate) -> Agent:
        agent = Agent(project_id=project_id, **data.model_dump())
        self._db.add(agent)
        await self._db.commit()
        await self._db.refresh(agent)
        return agent

    async def list_for_project(self, project_id: uuid.UUID) -> list[Agent]:
        result = await self._db.execute(select(Agent).where(Agent.project_id == project_id))
        return list(result.scalars().all())

    async def get_owned(self, agent_id: uuid.UUID, *, project_id: uuid.UUID) -> Agent:
        agent = await self._db.get(Agent, agent_id)
        if not agent or agent.project_id != project_id:
            raise NotFoundError("Agent not found")
        return agent

    async def update(self, agent_id: uuid.UUID, *, project_id: uuid.UUID, data: AgentUpdate) -> Agent:
        agent = await self.get_owned(agent_id, project_id=project_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(agent, field, value)
        await self._db.commit()
        await self._db.refresh(agent)
        return agent

    async def delete(self, agent_id: uuid.UUID, *, project_id: uuid.UUID) -> None:
        agent = await self.get_owned(agent_id, project_id=project_id)
        await self._db.delete(agent)
        await self._db.commit()
