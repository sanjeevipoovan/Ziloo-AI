"""
POST /v1/chat/completions

The one literal, top-level path named by the spec's Expected Result
section. Everything else (models, RAG, persistence) is wired in via the
Orchestrator; this route stays thin: resolve the caller's project,
validate the request, delegate, and - for streaming - turn orchestrator
events into an SSE response.
"""
import json
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Principal, get_resolved_project_id
from app.core.exceptions import NotFoundError
from app.db.models.conversation import Conversation
from app.db.session import get_db
from app.middleware.rate_limit import enforce_rate_limit
from app.orchestrator.orchestrator import Orchestrator, get_orchestrator
from app.schemas.chat import ChatCompletionRequest

router = APIRouter(prefix="/v1/chat", tags=["chat"])


async def _resolve_project_id(payload: ChatCompletionRequest, principal: Principal, db: AsyncSession) -> uuid.UUID:
    return await get_resolved_project_id(project_id=payload.project_id, principal=principal, db=db)


async def _validate_conversation(payload: ChatCompletionRequest, project_id: uuid.UUID, db: AsyncSession) -> None:
    if not payload.conversation_id:
        return
    conversation = await db.get(Conversation, payload.conversation_id)
    if not conversation or conversation.project_id != project_id:
        raise NotFoundError("Conversation not found")


@router.post("/completions")
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
    principal: Principal = Depends(enforce_rate_limit),
    db: AsyncSession = Depends(get_db),
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    request_id = request.state.request_id
    project_id = await _resolve_project_id(payload, principal, db)
    await _validate_conversation(payload, project_id, db)

    if payload.stream:
        return StreamingResponse(
            _stream_events(payload, principal.user_id, project_id, request_id, orchestrator),
            media_type="text/event-stream",
            headers={"X-Request-ID": request_id, "Cache-Control": "no-cache"},
        )

    return await orchestrator.run_chat(
        payload=payload, user_id=principal.user_id, project_id=project_id, request_id=request_id
    )


async def _stream_events(payload, user_id, project_id, request_id, orchestrator: Orchestrator):
    try:
        async for event in orchestrator.stream_chat(
            payload=payload, user_id=user_id, project_id=project_id, request_id=request_id
        ):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as exc:  # noqa: BLE001 - last-resort guard so the stream always terminates cleanly
        error_event = {"error": {"code": "STREAM_ERROR", "message": str(exc), "request_id": request_id}}
        yield f"data: {json.dumps(error_event)}\n\n"
    finally:
        yield "data: [DONE]\n\n"
