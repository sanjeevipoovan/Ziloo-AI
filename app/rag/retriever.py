import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.rag.embeddings import EmbeddingClient


class Retriever:
    def __init__(self, db: AsyncSession, embedding_client: EmbeddingClient | None = None):
        self._db = db
        self.embeddings = embedding_client or EmbeddingClient()

    async def retrieve(
        self, *, knowledge_base_id: uuid.UUID, query: str, top_k: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        """Returns (chunk, similarity_score) pairs, highest similarity first.
        pgvector's cosine_distance() is 0 (identical) to 2 (opposite); we
        report `1 - distance` as an intuitive similarity score."""
        query_vector = await self.embeddings.embed_one(query)
        distance = DocumentChunk.embedding.cosine_distance(query_vector)

        result = await self._db.execute(
            select(DocumentChunk, distance.label("distance"))
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .order_by(distance)
            .limit(top_k)
        )
        return [(chunk, 1 - dist) for chunk, dist in result.all()]
