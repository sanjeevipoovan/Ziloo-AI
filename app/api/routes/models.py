from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.registry import ModelRegistry
from app.schemas.model import ModelOut

router = APIRouter(prefix="/v1/models", tags=["models"])


@router.get("", response_model=list[ModelOut])
async def list_models(db: AsyncSession = Depends(get_db)):
    return await ModelRegistry(db).list_active()
