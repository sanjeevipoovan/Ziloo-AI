"""
Knowledge base management + document upload/retrieval.

Upload -> parse -> chunk -> embed -> pgvector happens via FastAPI's
BackgroundTasks, not Celery (per the spec: no background-worker
infrastructure until there's a real workload that needs it). The
document's `status` field (pending -> processing -> ready|failed) lets
clients poll instead of blocking the upload request on embedding calls.
"""
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_resolved_project_id
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.db.models.knowledge_base import KnowledgeBase
from app.db.session import AsyncSessionLocal, get_db
from app.rag.chunker import chunk_text
from app.rag.embeddings import EmbeddingClient
from app.rag.loader import UnsupportedFileTypeError, load_text
from app.rag.retriever import Retriever
from app.schemas.knowledge import DocumentOut, KnowledgeBaseCreate, KnowledgeBaseOut, RetrievalQuery, RetrievedChunk

router = APIRouter(prefix="/v1/knowledge", tags=["knowledge"])
settings = get_settings()


async def _get_owned_kb(kb_id: uuid.UUID, project_id: uuid.UUID, db: AsyncSession) -> KnowledgeBase:
    kb = await db.get(KnowledgeBase, kb_id)
    if not kb or kb.project_id != project_id:
        raise NotFoundError("Knowledge base not found")
    return kb


@router.post("/bases", response_model=KnowledgeBaseOut, status_code=201)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    kb = KnowledgeBase(project_id=project_id, name=payload.name, description=payload.description)
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return kb


@router.get("/bases", response_model=list[KnowledgeBaseOut])
async def list_knowledge_bases(
    project_id: uuid.UUID = Depends(get_resolved_project_id), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.project_id == project_id))
    return list(result.scalars().all())


@router.post("/bases/{kb_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    kb_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_kb(kb_id, project_id, db)

    contents = await file.read()
    if len(contents) / (1024 * 1024) > settings.MAX_UPLOAD_SIZE_MB:
        raise ValidationAppError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit")

    suffix = Path(file.filename or "upload").suffix.lower()
    tmp_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}{suffix}"
    tmp_path.write_bytes(contents)

    document = Document(
        knowledge_base_id=kb_id,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        status="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    background_tasks.add_task(_process_document, document.id, str(tmp_path))
    return document


async def _process_document(document_id: uuid.UUID, tmp_path: str) -> None:
    """Runs after the HTTP response is sent. Uses its own DB session since
    the request-scoped session is closed by then."""
    async with AsyncSessionLocal() as db:
        document = await db.get(Document, document_id)
        if not document:
            Path(tmp_path).unlink(missing_ok=True)
            return
        try:
            document.status = "processing"
            await db.commit()

            text_content = load_text(tmp_path)
            chunks = chunk_text(text_content)
            vectors = await EmbeddingClient().embed(chunks)

            for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                db.add(DocumentChunk(document_id=document_id, chunk_index=idx, content=chunk, embedding=vector))

            document.status = "ready"
            await db.commit()
        except (UnsupportedFileTypeError, Exception):
            await db.rollback()
            document.status = "failed"
            await db.commit()
        finally:
            Path(tmp_path).unlink(missing_ok=True)


@router.get("/bases/{kb_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    kb_id: uuid.UUID,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_kb(kb_id, project_id, db)
    result = await db.execute(select(Document).where(Document.knowledge_base_id == kb_id))
    return list(result.scalars().all())


@router.post("/bases/{kb_id}/retrieve", response_model=list[RetrievedChunk])
async def retrieve(
    kb_id: uuid.UUID,
    payload: RetrievalQuery,
    project_id: uuid.UUID = Depends(get_resolved_project_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_kb(kb_id, project_id, db)
    results = await Retriever(db).retrieve(knowledge_base_id=kb_id, query=payload.query, top_k=payload.top_k)
    return [
        RetrievedChunk(document_id=c.document_id, chunk_index=c.chunk_index, content=c.content, score=score)
        for c, score in results
    ]
