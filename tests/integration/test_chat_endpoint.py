from tests.fakes import FailingProvider
from tests.integration.conftest import clear_overrides, make_client, register_and_login


async def test_chat_completion_with_user_auth(db_session):
    async with make_client(db_session) as client:
        headers = await register_and_login(client, "carol@example.com")
        project = (await client.post("/v1/projects", json={"name": "Test Project"}, headers=headers)).json()

        resp = await client.post(
            "/v1/chat/completions",
            json={
                "model": "glm-5.2",
                "messages": [{"role": "user", "content": "Hello"}],
                "project_id": project["id"],
            },
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["model"] == "glm-5.2"
        assert body["choices"][0]["message"]["role"] == "assistant"
        assert body["usage"]["total_tokens"] > 0
    clear_overrides()


async def test_chat_completion_with_api_key(db_session):
    async with make_client(db_session) as client:
        headers = await register_and_login(client, "dave@example.com")
        project = (await client.post("/v1/projects", json={"name": "Dave Project"}, headers=headers)).json()
        key_resp = await client.post(f"/v1/projects/{project['id']}/api-keys", json={"name": "ci-key"}, headers=headers)
        api_key = key_resp.json()["key"]

        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "auto", "messages": [{"role": "user", "content": "hi there"}]},
            headers={"X-API-Key": api_key},
        )

        assert resp.status_code == 200
        assert resp.json()["model"] == "glm-5.2"  # short message -> auto-routes to glm
    clear_overrides()


async def test_chat_completion_rejects_missing_auth(db_session):
    async with make_client(db_session) as client:
        resp = await client.post(
            "/v1/chat/completions", json={"model": "glm-5.2", "messages": [{"role": "user", "content": "hi"}]}
        )
        assert resp.status_code == 401
    clear_overrides()


async def test_chat_completion_handles_provider_failure(db_session):
    async with make_client(db_session, provider=FailingProvider()) as client:
        headers = await register_and_login(client, "erin@example.com")
        project = (await client.post("/v1/projects", json={"name": "Erin Project"}, headers=headers)).json()

        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "glm-5.2", "messages": [{"role": "user", "content": "hi"}], "project_id": project["id"]},
            headers=headers,
        )

        assert resp.status_code in (502, 503)
        assert resp.json()["error"]["code"] in ("MODEL_UNAVAILABLE", "PROVIDER_ERROR")
    clear_overrides()


async def test_streaming_chat_completion(db_session):
    async with make_client(db_session) as client:
        headers = await register_and_login(client, "frank@example.com")
        project = (await client.post("/v1/projects", json={"name": "Frank Project"}, headers=headers)).json()

        async with client.stream(
            "POST",
            "/v1/chat/completions",
            json={
                "model": "glm-5.2",
                "messages": [{"role": "user", "content": "hi"}],
                "project_id": project["id"],
                "stream": True,
            },
            headers=headers,
        ) as resp:
            assert resp.status_code == 200
            lines = [line async for line in resp.aiter_lines() if line.strip()]

        assert any("model_selected" in line for line in lines)
        assert any("response_started" in line for line in lines)
        assert any("[DONE]" in line for line in lines)
    clear_overrides()
