from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# NullPool-style pooling is intentionally NOT used here - this is the
# application's steady-state connection pool, tuned via DB_POOL_* settings
# per the spec's database-security requirements (bounded pool size,
# overflow, timeout, pre-ping to drop stale connections).
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """The single canonical DB session dependency. Every other dependency
    or factory that needs a session (api/dependencies.py, the orchestrator
    factory, ...) builds on this one function so tests can override it in
    exactly one place."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
