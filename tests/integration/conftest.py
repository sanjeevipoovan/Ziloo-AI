"""
Why httpx.AsyncClient + ASGITransport instead of fastapi.testclient.TestClient:

Starlette's synchronous TestClient runs the ASGI app through its own
internal event-loop handling, which can end up on a different event loop
than the one pytest-asyncio used to create the `db_session` fixture's
aiosqlite connection. aiosqlite connections are bound to the loop they
were created on, so mixing them with TestClient can produce
"attached to a different loop" errors. Using httpx.AsyncClient with
ASGITransport inside an `async def` test keeps the fixture and every HTTP
call on the exact same event loop.
"""
import httpx

from app.db.session import get_db
from app.main import app
from app.orchestrator.orchestrator import Orchestrator, get_orchestrator
from tests.fakes import FakeProvider


def make_client(db_session, provider=None) -> httpx.AsyncClient:
    async def _override_get_db():
        yield db_session

    async def _override_get_orchestrator():
        return Orchestrator(db_session, provider=provider or FakeProvider())

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_orchestrator] = _override_get_orchestrator

    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def clear_overrides():
    app.dependency_overrides.clear()


async def register_and_login(client: httpx.AsyncClient, email: str, password: str = "supersecret123") -> dict:
    await client.post("/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
