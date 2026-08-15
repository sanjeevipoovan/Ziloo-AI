"""
Rate limiting dependency (not raw ASGI middleware) because the limit key
is per-API-key/per-project, which is only known after authentication runs.
Compose this into a route via `Depends(enforce_rate_limit)` in place of
`Depends(get_current_principal)` to get both auth and rate limiting.
"""
from fastapi import Depends, Request

from app.api.dependencies import Principal, get_current_principal
from app.core.config import get_settings
from app.core.exceptions import RateLimitError
from app.services.rate_limit_service import RateLimitService

settings = get_settings()


async def enforce_rate_limit(
    request: Request,
    principal: Principal = Depends(get_current_principal),
) -> Principal:
    service = RateLimitService()
    key = str(principal.project_id or principal.user_id or (request.client.host if request.client else "unknown"))

    allowed, remaining = await service.check(key=key, limit_per_minute=settings.RATE_LIMIT_DEFAULT_PER_MINUTE)
    request.state.rate_limit_remaining = remaining

    if not allowed:
        raise RateLimitError()

    return principal
