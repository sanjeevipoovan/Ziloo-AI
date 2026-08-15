"""
Orchestrator.

    User request
        v
    Load agent configuration (optional)
        v
    Build context (system prompt + conversation + RAG context)
        v
    Model Router
        v
    Selected model -> Execution Engine -> Response
        v
    Persist conversation + usage

Routes stay thin and call into this; this is the one component that knows
the full request lifecycle end-to-end. Deliberately not a multi-agent
framework - one agent, one model call, one response - but every seam
(context building, execution, persistence) is its own component so a
future version can add multi-step tool use without a rewrite.
"""
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent import Agent
from app.db.session import get_db
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator.context import ContextBuilder
from app.orchestrator.execution import ExecutionEngine
from app.providers.base import LLMProvider, ProviderMessage
from app.providers.huggingface import HuggingFaceProvider
from app.rag.retriever import Retriever
from app.schemas.chat import ChatChoice, ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatUsage
from app.services.conversation_service import ConversationService
from app.services.usage_service import UsageService


class Orchestrator:
    def __init__(self, db: AsyncSession, provider: LLMProvider | None = None):
        self._db = db
        self._registry = ModelRegistry(db)
        self._router = ModelRouter(self._registry)
        self._context_builder = ContextBuilder()
        # `provider` is injectable so tests can supply a fake without
        # monkeypatching - see tests/fakes.py and get_orchestrator below.
        self._provider = provider or HuggingFaceProvider()
        self._execution = ExecutionEngine(self._provider)
        self._conversations = ConversationService(db)
        self._usage = UsageService(db)

    async def run_chat(
        self,
        *,
        payload: ChatCompletionRequest,
        user_id: uuid.UUID | None,
        project_id: uuid.UUID | None,
        request_id: str,
        agent: Agent | None = None,
    ) -> ChatCompletionResponse:
        decision = await self._router.resolve(payload.model, [m.content for m in payload.messages])
        retrieved_chunks = await self._maybe_retrieve(payload, agent)
        provider_messages = self._assemble_messages(payload, retrieved_chunks, agent)

        status = "success"
        start = time.monotonic()
        try:
            result = await self._execution.run(
                model_identifier=decision.model.model_identifier,
                messages=provider_messages,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
            )
        except Exception:
            status = "error"
            raise
        finally:
            await self._usage.record(
                project_id=project_id,
                user_id=user_id,
                model_id=decision.model.id,
                provider=self._provider.name,
                input_tokens=None,
                output_tokens=None,
                latency_ms=int((time.monotonic() - start) * 1000),
                status=status,
                request_id=request_id,
            )

        if payload.conversation_id:
            await self._conversations.append_exchange(
                conversation_id=payload.conversation_id,
                user_content=payload.messages[-1].content,
                assistant_content=result.response.content,
                model_name=decision.model.name,
                input_tokens=result.response.usage.prompt_tokens,
                output_tokens=result.response.usage.completion_tokens,
            )

        return ChatCompletionResponse(
            id=f"chatcmpl_{uuid.uuid4().hex}",
            request_id=request_id,
            model=decision.model.name,
            provider=self._provider.name,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=result.response.content),
                    finish_reason=result.response.finish_reason,
                )
            ],
            usage=ChatUsage(
                prompt_tokens=result.response.usage.prompt_tokens,
                completion_tokens=result.response.usage.completion_tokens,
                total_tokens=result.response.usage.total_tokens,
            ),
            conversation_id=payload.conversation_id,
        )

    async def stream_chat(
        self,
        *,
        payload: ChatCompletionRequest,
        user_id: uuid.UUID | None,
        project_id: uuid.UUID | None,
        request_id: str,
        agent: Agent | None = None,
    ) -> AsyncIterator[dict]:
        decision = await self._router.resolve(payload.model, [m.content for m in payload.messages])
        yield {"type": "model_selected", "model": decision.model.name, "reason": decision.reason}

        retrieved_chunks = None
        if payload.knowledge_base_id or (agent and agent.tool_config.get("knowledge_base_id")):
            yield {"type": "retrieval_started"}
            retrieved_chunks = await self._maybe_retrieve(payload, agent)
            yield {"type": "retrieval_completed", "chunks_found": len(retrieved_chunks or [])}

        provider_messages = self._assemble_messages(payload, retrieved_chunks, agent)
        yield {"type": "response_started", "request_id": request_id}

        full_content: list[str] = []
        final_usage: dict | None = None
        status = "success"
        start = time.monotonic()
        try:
            async for event in self._execution.run_stream(
                model_identifier=decision.model.model_identifier,
                messages=provider_messages,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
            ):
                if event["type"] == "delta":
                    full_content.append(event["content"])
                elif event["type"] == "response_completed":
                    final_usage = event.get("usage")
                yield event
        except Exception:
            status = "error"
            yield {"type": "error", "message": "The model provider returned an error", "request_id": request_id}
            return
        finally:
            await self._usage.record(
                project_id=project_id,
                user_id=user_id,
                model_id=decision.model.id,
                provider=self._provider.name,
                input_tokens=(final_usage or {}).get("prompt_tokens"),
                output_tokens=(final_usage or {}).get("completion_tokens"),
                latency_ms=int((time.monotonic() - start) * 1000),
                status=status,
                request_id=request_id,
            )

        if payload.conversation_id:
            await self._conversations.append_exchange(
                conversation_id=payload.conversation_id,
                user_content=payload.messages[-1].content,
                assistant_content="".join(full_content),
                model_name=decision.model.name,
                input_tokens=(final_usage or {}).get("prompt_tokens"),
                output_tokens=(final_usage or {}).get("completion_tokens"),
            )

    async def _maybe_retrieve(self, payload: ChatCompletionRequest, agent: Agent | None) -> list[str] | None:
        kb_id = payload.knowledge_base_id or (agent.tool_config.get("knowledge_base_id") if agent else None)
        if not kb_id:
            return None
        if isinstance(kb_id, str):
            kb_id = uuid.UUID(kb_id)
        retriever = Retriever(self._db)
        results = await retriever.retrieve(knowledge_base_id=kb_id, query=payload.messages[-1].content)
        return [chunk.content for chunk, _score in results]

    def _assemble_messages(
        self, payload: ChatCompletionRequest, retrieved_chunks: list[str] | None, agent: Agent | None
    ) -> list[ProviderMessage]:
        context = self._context_builder.build(
            user_input=payload.messages[-1].content,
            agent=agent,
            retrieved_chunks=retrieved_chunks,
        )
        history = [ProviderMessage(role=m.role, content=m.content) for m in payload.messages]
        return [context.messages[0], *history]


async def get_orchestrator(db: AsyncSession = Depends(get_db)) -> Orchestrator:
    return Orchestrator(db)
