from tests.integration.conftest import clear_overrides, make_client, register_and_login


async def test_create_and_run_agent(db_session):
    async with make_client(db_session) as client:
        headers = await register_and_login(client, "ivan@example.com")
        project = (await client.post("/v1/projects", json={"name": "Ivan Project"}, headers=headers)).json()

        agent_resp = await client.post(
            f"/v1/agents?project_id={project['id']}",
            json={"name": "Support Bot", "system_prompt": "You are a support agent.", "model_policy": "glm-5.2"},
            headers=headers,
        )
        assert agent_resp.status_code == 201
        agent_id = agent_resp.json()["id"]

        run_resp = await client.post(
            f"/v1/agents/{agent_id}/run?project_id={project['id']}",
            json={"input": "I need help with my order"},
            headers=headers,
        )
        assert run_resp.status_code == 200
        body = run_resp.json()
        assert body["model"] == "glm-5.2"
        assert body["choices"][0]["message"]["content"]
    clear_overrides()


async def test_agent_update_and_delete(db_session):
    async with make_client(db_session) as client:
        headers = await register_and_login(client, "judy@example.com")
        project = (await client.post("/v1/projects", json={"name": "Judy Project"}, headers=headers)).json()

        agent = (
            await client.post(
                f"/v1/agents?project_id={project['id']}",
                json={"name": "Bot", "system_prompt": "hi"},
                headers=headers,
            )
        ).json()

        patched = await client.patch(
            f"/v1/agents/{agent['id']}?project_id={project['id']}", json={"temperature": 0.2}, headers=headers
        )
        assert patched.status_code == 200
        assert patched.json()["temperature"] == 0.2

        deleted = await client.delete(f"/v1/agents/{agent['id']}?project_id={project['id']}", headers=headers)
        assert deleted.status_code == 204
    clear_overrides()
