import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.conversation import Conversation
from app.db.models.message import Message


class ConversationService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self, *, project_id: uuid.UUID, user_id: uuid.UUID | None, title: str | None, agent_id: uuid.UUID | None
    ) -> Conversation:
        conversation = Conversation(project_id=project_id, user_id=user_id, title=title, agent_id=agent_id)
        self._db.add(conversation)
        await self._db.commit()
        await self._db.refresh(conversation)
        return conversation

    async def get_owned(self, conversation_id: uuid.UUID, *, project_id: uuid.UUID) -> Conversation:
        conversation = await self._db.get(Conversation, conversation_id)
        if not conversation or conversation.project_id != project_id:
            raise NotFoundError("Conversation not found")
        return conversation

    async def get_with_messages(self, conversation_id: uuid.UUID, *, project_id: uuid.UUID) -> Conversation:
        conversation = await self.get_owned(conversation_id, project_id=project_id)
        await self._db.refresh(conversation, attribute_names=["messages"])
        return conversation

    async def list_for_project(self, project_id: uuid.UUID) -> list[Conversation]:
        result = await self._db.execute(
            select(Conversation).where(Conversation.project_id == project_id).order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, conversation_id: uuid.UUID, *, project_id: uuid.UUID) -> None:
        conversation = await self.get_owned(conversation_id, project_id=project_id)
        await self._db.delete(conversation)
        await self._db.commit()

    async def append_exchange(
        self,
        *,
        conversation_id: uuid.UUID,
        user_content: str,
        assistant_content: str,
        model_name: str,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> None:
        """Used by the orchestrator after a successful (or streamed) model
        call. Intentionally does NOT re-validate project ownership - the
        caller (the chat route, via get_resolved_project_id) already did
        that before invoking the orchestrator."""
        conversation = await self._db.get(Conversation, conversation_id)
        if not conversation:
            raise NotFoundError("Conversation not found")

        self._db.add(Message(conversation_id=conversation_id, role="user", content=user_content))
        self._db.add(
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_content,
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        )
        await self._db.commit()
