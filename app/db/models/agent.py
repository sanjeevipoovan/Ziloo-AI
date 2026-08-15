import uuid

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Agent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agents"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # "auto" | an explicit model name (e.g. "kimi-k3") registered in the Model Registry
    model_policy: Mapped[str] = mapped_column(String(50), default="auto", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024, nullable=False)
    max_steps: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Generic tool/config bag, e.g. {"knowledge_base_id": "..."} to enable RAG
    # for this agent. Deliberately untyped at the DB layer so new tool types
    # don't require a migration.
    tool_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="agents")
