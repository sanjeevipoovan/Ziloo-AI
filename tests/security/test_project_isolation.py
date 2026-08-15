"""IDOR prevention: a user (or an API key) must never reach another
project's resources, regardless of guessing a valid UUID."""
from tests.integration.conftest import clear_overrides, make_client, register_and_login


async def test_user_cannot_access_another_users_project(db_session):
    async with make_client(db_session) as client:
        headers_a = await register_and_login(client, "userA@example.com")
        project_a = (await client.post("/v1/projects", json={"name": "A's project"}, headers=headers_a)).json()

        headers_b = await register_and_login(client, "userB@example.com")
        resp = await client.get(f"/v1/projects/{project_a['id']}", headers=headers_b)

        assert resp.status_code in (403, 404)
    clear_overrides()


async def test_user_cannot_create_agent_in_another_users_project(db_session):
    async with make_client(db_session) as client:
        headers_a = await register_and_login(client, "userC@example.com")
        project_a = (await client.post("/v1/projects", json={"name": "C's project"}, headers=headers_a)).json()

        headers_b = await register_and_login(client, "userD@example.com")
        resp = await client.post(
            f"/v1/agents?project_id={project_a['id']}",
            json={"name": "sneaky agent", "system_prompt": "hi"},
            headers=headers_b,
        )
        assert resp.status_code in (403, 404)
    clear_overrides()


async def test_api_key_is_scoped_to_its_own_project(db_session):
    async with make_client(db_session) as client:
        headers_a = await register_and_login(client, "userE@example.com")
        project_a = (await client.post("/v1/projects", json={"name": "E project A"}, headers=headers_a)).json()
        project_b = (await client.post("/v1/projects", json={"name": "E project B"}, headers=headers_a)).json()

        api_key = (
            await client.post(f"/v1/projects/{project_a['id']}/api-keys", json={"name": "k"}, headers=headers_a)
        ).json()["key"]

        resp = await client.get(f"/v1/agents?project_id={project_b['id']}", headers={"X-API-Key": api_key})
        assert resp.status_code in (403, 404)
    clear_overrides()


async def test_user_cannot_read_another_users_conversation(db_session):
    async with make_client(db_session) as client:
        headers_a = await register_and_login(client, "userF@example.com")
        project_a = (await client.post("/v1/projects", json={"name": "F project"}, headers=headers_a)).json()
        conv = (
            await client.post(f"/v1/conversations?project_id={project_a['id']}", json={}, headers=headers_a)
        ).json()

        headers_b = await register_and_login(client, "userG@example.com")
        project_b = (await client.post("/v1/projects", json={"name": "G project"}, headers=headers_b)).json()

        # userG tries to read userF's conversation by ID, scoped under their OWN project
        resp = await client.get(f"/v1/conversations/{conv['id']}?project_id={project_b['id']}", headers=headers_b)
        assert resp.status_code == 404
    clear_overrides()
