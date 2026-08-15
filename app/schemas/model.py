import uuid

from pydantic import BaseModel, ConfigDict


class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    model_type: str
    context_window: int
    capabilities: list[str]
    is_active: bool
