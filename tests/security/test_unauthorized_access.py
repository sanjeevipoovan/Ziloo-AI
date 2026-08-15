from tests.integration.conftest import clear_overrides, make_client, register_and_login


async def test_invalid_api_key_is_rejected(db_session):
    async with make_client(db_session) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "glm-5.2", "messages": [{"role": "user", "content": "hi"}]},
            headers={"X-API-Key": "myai_not_a_real_key"},
        )
        assert resp.status_code == 401
    clear_overrides()


async def test_revoked_api_key_is_rejected(db_session):
    async with make_client(db_session) as client:
        headers = await register_and_login(client, "frank2@example.com")
        project = (await client.post("/v1/projects", json={"name": "F project"}, headers=headers)).json()
        key_resp = (
            await client.post(f"/v1/projects/{project['id']}/api-keys", json={"name": "k"}, headers=headers)
        ).json()
        api_key, key_id = key_resp["key"], key_resp["id"]

        await client.delete(f"/v1/projects/{project['id']}/api-keys/{key_id}", headers=headers)

        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "glm-5.2", "messages": [{"role": "user", "content": "hi"}]},
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 401
    clear_overrides()


async def test_malformed_jwt_is_rejected(db_session):
    async with make_client(db_session) as client:
        resp = await client.get("/v1/users/me", headers={"Authorization": "Bearer not-a-real-jwt"})
        assert resp.status_code == 401
    clear_overrides()


async def test_missing_credentials_is_rejected(db_session):
    async with make_client(db_session) as client:
        resp = await client.get("/v1/projects")
        assert resp.status_code == 401
    clear_overrides()


async def test_rate_limit_returns_429(db_session, monkeypatch):
    from app.middleware import rate_limit as rate_limit_module

    class AlwaysBlockedRateLimiter:
        async def check(self, *, key, limit_per_minute):
            return False, 0

    monkeypatch.setattr(rate_limit_module, "RateLimitService", lambda: AlwaysBlockedRateLimiter())

    async with make_client(db_session) as client:
        headers = await register_and_login(client, "grace2@example.com")
        project = (await client.post("/v1/projects", json={"name": "G project"}, headers=headers)).json()

        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "glm-5.2", "messages": [{"role": "user", "content": "hi"}], "project_id": project["id"]},
            headers=headers,
        )
        assert resp.status_code == 429
    clear_overrides()
