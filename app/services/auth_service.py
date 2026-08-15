from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def register(self, *, email: str, password: str, full_name: str | None) -> User:
        existing = await self._db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ConflictError("An account with this email already exists")

        user = User(email=email, hashed_password=hash_password(password), full_name=full_name)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def authenticate(self, *, email: str, password: str) -> User:
        result = await self._db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is inactive")
        return user

    @staticmethod
    def issue_token(user: User) -> str:
        return create_access_token(subject=str(user.id))
