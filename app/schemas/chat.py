import uuid
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatCompletionRequest(BaseModel):
    # "auto" | "glm-5.2" | "kimi-k3" | any other name registered in the
    # Model Registry. The API never assumes these two are the only options.
    model: str = "auto"
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=32000)
    stream: bool = False
    conversation_id: uuid.UUID | None = None
    # Required when authenticating as a human user (a JWT isn't scoped to
    # one project); ignored/validated against the key's own project when
    # authenticating with a MyAI API key. See api/dependencies.get_resolved_project_id.
    project_id: uuid.UUID | None = None
    # Optional: ground the response in a knowledge base via RAG.
    knowledge_base_id: uuid.UUID | None = None


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str | None


class ChatCompletionResponse(BaseModel):
    id: str
    request_id: str
    model: str
    provider: str
    choices: list[ChatChoice]
    usage: ChatUsage
    conversation_id: uuid.UUID | None = None
