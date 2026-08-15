import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str | None = None
    agent_id: uuid.UUID | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    agent_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = []
