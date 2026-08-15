"""
Authentication & authorization dependencies.

Two authentication mechanisms, one shared downstream shape:
  - Human users authenticate with a JWT bearer token.
  - External applications authenticate with a MyAI API key (X-API-Key
    header, or a bearer token prefixed "myai_").

Both resolve to a `Principal`, so route handlers and services don't need
to branch on how the caller authenticated - they just ask "what project
can this principal touch". `require_project_access` /
`get_resolved_project_id` are the single choke point every project-scoped
resource goes through; this is the IDOR guard the spec calls for in
section 7 ("Users must never be able to access another user's project,
agent, conversation, document or API key").
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError, NotFoundError, ValidationAppError
from app.core.security import decode_access_token, hash_api_key
from app.db.models.api_key import APIKey
from app.db.models.project import Project
from app.db.models.user import User
from app.db.session import get_db

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class Principal:
    kind: str  # "user" | "api_key"
    user_id: uuid.UUID | None
    project_id: uuid.UUID | None  # only set for api_key principals
    api_key_id: uuid.UUID | None
    scopes: list[str]


async def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Principal:
    api_key_value = x_api_key
    if api_key_value is None and credentials and credentials.credentials.startswith("myai_"):
        api_key_value = credentials.credentials

    if api_key_value:
        return await _authenticate_api_key(api_key_value, db)

    if credentials:
        return await _authenticate_jwt(credentials.credentials, db)

    raise AuthenticationError("Missing credentials: provide a Bearer JWT or an X-API-Key header")


async def _authenticate_jwt(token: str, db: AsyncSession) -> Principal:
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise AuthenticationError("Invalid or expired token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    try:
        user = await db.get(User, uuid.UUID(user_id))
    except ValueError as exc:
        raise AuthenticationError("Invalid token payload") from exc

    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    return Principal(kind="user", user_id=user.id, project_id=None, api_key_id=None, scopes=["*"])


async def _authenticate_api_key(raw_key: str, db: AsyncSession) -> Principal:
    key_hash = hash_api_key(raw_key)
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise AuthenticationError("Invalid API key")
    if api_key.revoked_at is not None:
        raise AuthenticationError("API key has been revoked")
    if api_key.expires_at is not None and api_key.expires_at < datetime.now(timezone.utc):
        raise AuthenticationError("API key has expired")

    api_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    return Principal(
        kind="api_key",
        user_id=None,
        project_id=api_key.project_id,
        api_key_id=api_key.id,
        scopes=api_key.scopes,
    )


async def require_project_access(project_id: uuid.UUID, principal: Principal, db: AsyncSession) -> Project:
    """Central IDOR guard. Every project-scoped resource - directly or
    indirectly (an agent, a conversation, a knowledge base, an API key) -
    must be reachable only after this check passes for its owning project."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")

    if principal.kind == "api_key":
        if principal.project_id != project.id:
            raise AuthorizationError("This API key cannot access this project")
        return project

    user = await db.get(User, principal.user_id)
    same_org = user is not None and user.organization_id is not None and user.organization_id == project.organization_id
    if project.owner_id != principal.user_id and not same_org:
        raise AuthorizationError("You do not have access to this project")
    return project


async def get_resolved_project_id(
    project_id: uuid.UUID | None = None,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    """Resolves the effective project_id for a request:
      - API-key principals are pinned to their key's own project. If a
        project_id was also supplied and disagrees, that's a hard error
        rather than silently preferring one or the other.
      - User (JWT) principals must supply project_id explicitly (a JWT
        isn't scoped to a single project), and it's verified via
        require_project_access.
    """
    if principal.kind == "api_key":
        if project_id is not None and project_id != principal.project_id:
            raise AuthorizationError("This API key cannot access the requested project")
        return principal.project_id

    if project_id is None:
        raise ValidationAppError("project_id is required when authenticating as a user")

    await require_project_access(project_id, principal, db)
    return project_id
