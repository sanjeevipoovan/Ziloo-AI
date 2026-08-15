import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Principal, get_current_principal, get_resolved_project_id
from app.db.session import get_db
from app.orchestrator.orchestrator import Orchestrator, get_orchestrator
from app.schemas.agent import AgentCreate, AgentOut, AgentRunRequest, AgentUpdate
from app.schemas.chat import ChatCompletionResponse, ChatCompletionRequest, ChatMessage
from app.services.agent_service import AgentService

router = APIRouter(prefix="/v1/agents", tags=["agents"])


@router.post("", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    return await AgentService(db).create(project_id=project_id, data=payload)


@router.get("", response_model=list[AgentOut])
async def list_agents(project_id: uuid.UUID = Depends(get_resolved_project_id), db: AsyncSession = Depends(get_db)):
    return await AgentService(db).list_for_project(project_id)


@router.get("/{agent_id}", response_model=AgentOut)
async def get_agent(
    agent_id: uuid.UUID,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    return await AgentService(db).get_owned(agent_id, project_id=project_id)


@router.patch("/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: uuid.UUID,
    payload: AgentUpdate,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    return await AgentService(db).update(agent_id, project_id=project_id, data=payload)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: uuid.UUID,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    await AgentService(db).delete(agent_id, project_id=project_id)


@router.post("/{agent_id}/run", response_model=ChatCompletionResponse)
async def run_agent(
    agent_id: uuid.UUID,
    payload: AgentRunRequest,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    agent = await AgentService(db).get_owned(agent_id, project_id=project_id)

    chat_payload = ChatCompletionRequest(
        model=agent.model_policy,
        messages=[ChatMessage(role="user", content=payload.input)],
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        conversation_id=payload.conversation_id,
        project_id=project_id,
    )

    return await orchestrator.run_chat(
        payload=chat_payload,
        agent=agent,
        user_id=principal.user_id,
        project_id=project_id,
        request_id=f"req_{uuid.uuid4().hex}",
    )
