from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api.routes import agents, api_keys, auth, chat, conversations, health, knowledge, models, projects, users
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.seed import seed_defaults
from app.db.session import AsyncSessionLocal
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security import SecurityHeadersMiddleware

settings = get_settings()
configure_logging(debug=settings.DEBUG)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        integrations=[FastApiIntegration()],
        send_default_pii=False,  # never send secrets/credentials to Sentry
        traces_sample_rate=0.1 if settings.APP_ENV == "production" else 0.0,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seeding failure must never prevent the app from starting (e.g. so
    # /health/live can still respond during a transient DB issue at boot,
    # and so this stays robust under test harnesses that don't pre-migrate
    # the seed session's own database).
    try:
        async with AsyncSessionLocal() as session:
            await seed_defaults(session)
    except Exception:
        structlog.get_logger("myai.startup").warning("seed_defaults_failed", exc_info=True)
    yield


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(api_keys.router)
app.include_router(models.router)
app.include_router(agents.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(knowledge.router)
