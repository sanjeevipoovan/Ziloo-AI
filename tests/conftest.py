"""
Shared test fixtures.

Two things worth knowing before touching this file:

1. Env vars are set at MODULE level, before any `app.*` import anywhere in
   the test suite. Settings() (pydantic-settings) validates required
   fields (DATABASE_URL, JWT_SECRET, HF_API_TOKEN, GLM_MODEL_ID,
   KIMI_MODEL_ID) at import time via get_settings(), so if a test module
   imports `app.main` before these are set, the whole suite fails to
   collect. conftest.py is guaranteed to load first, so this is the one
   safe place to do it.

2. `db_session` uses an in-memory SQLite engine, NOT the real
   `DATABASE_URL` / `AsyncSessionLocal` from app.db.session (which the
   app's own startup lifespan uses to seed the registry against whatever
   DATABASE_URL is - here, a separate, empty in-memory SQLite DB, which is
   fine because main.py's lifespan seeding is wrapped in try/except and
   logs rather than raising on failure).

   pgvector's Vector column type has no SQLite equivalent, so
   `document_chunks` is deliberately excluded from `create_all` here.
   RAG/vector-search tests run against a real Postgres+pgvector instance
   instead - see tests/integration/test_rag.py.
"""
import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("JWT_SECRET", "test-secret-key-not-for-production")
os.environ.setdefault("HF_API_TOKEN", "hf_test_token")
os.environ.setdefault("GLM_MODEL_ID", "test-org/glm-test")
os.environ.setdefault("KIMI_MODEL_ID", "test-org/kimi-test")

import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.models.model import AIModel  # noqa: E402
from app.db.models.provider import Provider  # noqa: E402

_NON_SQLITE_TABLES = {"document_chunks"}


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    tables = [t for t in Base.metadata.sorted_tables if t.name not in _NON_SQLITE_TABLES]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        provider = Provider(name="huggingface", display_name="Hugging Face")
        session.add(provider)
        await session.flush()

        session.add(
            AIModel(
                name="glm-5.2", provider_id=provider.id, model_identifier="test-org/glm-test",
                model_type="chat", context_window=128000, capabilities=["general"], is_active=True,
            )
        )
        session.add(
            AIModel(
                name="kimi-k3", provider_id=provider.id, model_identifier="test-org/kimi-test",
                model_type="chat", context_window=256000, capabilities=["reasoning", "long_context"], is_active=True,
            )
        )
        await session.commit()

        yield session

    await engine.dispose()
