from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Provider(Base, UUIDMixin, TimestampMixin):
    """A model-serving backend, e.g. 'huggingface'. Adding vLLM, OpenAI, or
    a future self-hosted MyAI model later means inserting a new row here
    plus a new app/providers/<name>.py implementing LLMProvider - no schema
    change required."""

    __tablename__ = "providers"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    models: Mapped[list["AIModel"]] = relationship(back_populates="provider")
