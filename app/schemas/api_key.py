import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=lambda: ["chat:write"])
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class APIKeyCreated(BaseModel):
    """Returned exactly once, at creation time. `key` is the full plaintext
    API key - it cannot be retrieved again after this response."""

    id: uuid.UUID
    name: str
    key: str
    key_prefix: str
    scopes: list[str]
    expires_at: datetime | None


class APIKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    key_prefix: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    last_used_at: datetime | None
