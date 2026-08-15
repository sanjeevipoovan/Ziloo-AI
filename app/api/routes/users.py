from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Principal, get_current_principal
from app.core.exceptions import AuthorizationError
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import UserOut

router = APIRouter(prefix="/v1/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(principal: Principal = Depends(get_current_principal), db: AsyncSession = Depends(get_db)):
    if principal.kind != "user":
        raise AuthorizationError("This endpoint requires user authentication")
    user = await db.get(User, principal.user_id)
    return user
