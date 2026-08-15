"""
Embedding client for RAG. Uses Hugging Face's feature-extraction inference
task via the same huggingface_hub client family as the chat provider.

The embedding model is configuration-driven (settings.EMBEDDING_MODEL_ID)
like everything else. The default, sentence-transformers/all-MiniLM-L6-v2,
is a small, fast, widely-available 384-dimension model - EMBEDDING_DIMENSIONS
in app/core/config.py is set to match it. If you point EMBEDDING_MODEL_ID at
a model with a different output dimension, you must update EMBEDDING_DIMENSIONS
and write a new migration for document_chunks.embedding.
"""
from huggingface_hub import AsyncInferenceClient

from app.core.config import get_settings

settings = get_settings()


class EmbeddingClient:
    def __init__(self, model_id: str | None = None, token: str | None = None):
        self._model_id = model_id or settings.EMBEDDING_MODEL_ID
        self._client = AsyncInferenceClient(token=token or settings.HF_API_TOKEN)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = await self._client.feature_extraction(texts, model=self._model_id)
        # Normalize whatever numeric container comes back (numpy array,
        # nested list, ...) into plain list[list[float]] for pgvector.
        return [[float(x) for x in vector] for vector in vectors]

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.embed([text])
        return vectors[0]
