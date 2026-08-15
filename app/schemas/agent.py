import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    system_prompt: str = Field(min_length=1)
    model_policy: str = "auto"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=32000)
    max_steps: int = Field(default=1, ge=1, le=20)
    memory_enabled: bool = True
    tool_config: dict = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    model_policy: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=32000)
    max_steps: int | None = Field(default=None, ge=1, le=20)
    memory_enabled: bool | None = None
    tool_config: dict | None = None
    is_active: bool | None = None


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    system_prompt: str
    model_policy: str
    temperature: float
    max_tokens: int
    max_steps: int
    memory_enabled: bool
    tool_config: dict
    is_active: bool
    created_at: datetime


class AgentRunRequest(BaseModel):
    input: str = Field(min_length=1)
    conversation_id: uuid.UUID | None = None
