from tests.integration.conftest import clear_overrides, make_client


async def test_register_and_login(db_session):
    async with make_client(db_session) as client:
        register_resp = await client.post(
            "/v1/auth/register", json={"email": "alice@example.com", "password": "supersecret123", "full_name": "Alice"}
        )
        assert register_resp.status_code == 201
        assert register_resp.json()["email"] == "alice@example.com"

        login_resp = await client.post(
            "/v1/auth/login", json={"email": "alice@example.com", "password": "supersecret123"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        me_resp = await client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "alice@example.com"
    clear_overrides()


async def test_duplicate_registration_is_rejected(db_session):
    async with make_client(db_session) as client:
        await client.post("/v1/auth/register", json={"email": "dup@example.com", "password": "supersecret123"})
        resp = await client.post("/v1/auth/register", json={"email": "dup@example.com", "password": "anotherpass123"})
        assert resp.status_code == 409
    clear_overrides()


async def test_login_rejects_wrong_password(db_session):
    async with make_client(db_session) as client:
        await client.post("/v1/auth/register", json={"email": "bob@example.com", "password": "correctpassword"})
        resp = await client.post("/v1/auth/login", json={"email": "bob@example.com", "password": "wrongpassword"})
        assert resp.status_code == 401
    clear_overrides()
