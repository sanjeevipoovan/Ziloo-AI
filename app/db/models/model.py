import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class AIModel(Base, UUIDMixin, TimestampMixin):
    """A registered, callable model, e.g. 'glm-5.2'. `name` is the stable
    identifier the rest of the app (and API clients) use; `model_identifier`
    is the actual Hugging Face repo id, which comes from configuration at
    seed time (see app/db/seed.py) and can change without a code deploy."""

    __tablename__ = "models"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), default="chat", nullable=False)
    context_window: Mapped[int] = mapped_column(Integer, default=8192, nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    provider: Mapped["Provider"] = relationship(back_populates="models")
