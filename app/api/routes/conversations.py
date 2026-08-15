import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Principal, get_current_principal, get_resolved_project_id
from app.db.session import get_db
from app.schemas.conversation import ConversationCreate, ConversationDetailOut, ConversationOut
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    # user_id is None for conversations started by an external application
    # (API-key auth) - conversations are project-scoped, not user-scoped.
    return await ConversationService(db).create(
        project_id=project_id, user_id=principal.user_id, title=payload.title, agent_id=payload.agent_id
    )


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    project_id: uuid.UUID = Depends(get_resolved_project_id), db: AsyncSession = Depends(get_db)
):
    return await ConversationService(db).list_for_project(project_id)


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: uuid.UUID,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    return await ConversationService(db).get_with_messages(conversation_id, project_id=project_id)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    await ConversationService(db).delete(conversation_id, project_id=project_id)
