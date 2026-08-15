import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import EMBEDDING_DIMENSIONS
from app.db.base import Base, TimestampMixin, UUIDMixin


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    """A retrievable slice of a Document, with its embedding vector.

    NOTE: pgvector's Vector type is Postgres-specific and has no SQLite
    equivalent, so this table is intentionally excluded from the in-memory
    SQLite fixture used by most unit/integration tests - see
    tests/conftest.py and tests/integration/test_rag.py for how RAG is
    tested against a real Postgres+pgvector instance instead.
    """

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")
