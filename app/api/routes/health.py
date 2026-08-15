"""
Health endpoints. Readiness only gates on PostgreSQL (the "critical
dependency" per the spec) - a Hugging Face outage must not make the whole
API report unhealthy, since chat requests can still fail gracefully
per-request via ModelUnavailableError.
"""
from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness():
    return {"status": "ok"}


@router.get("/ready")
async def readiness():
    database_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False

    return {"status": "ready" if database_ok else "not_ready", "checks": {"database": database_ok}}
