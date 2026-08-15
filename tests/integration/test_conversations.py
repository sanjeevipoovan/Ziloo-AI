from tests.integration.conftest import clear_overrides, make_client, register_and_login


async def test_conversation_persists_messages_across_chat_calls(db_session):
    async with make_client(db_session) as client:
        headers = await register_and_login(client, "grace@example.com")
        project = (await client.post("/v1/projects", json={"name": "Grace Project"}, headers=headers)).json()

        conv = await client.post(
            f"/v1/conversations?project_id={project['id']}", json={"title": "First chat"}, headers=headers
        )
        assert conv.status_code == 201
        conversation_id = conv.json()["id"]

        await client.post(
            "/v1/chat/completions",
            json={
                "model": "glm-5.2", "messages": [{"role": "user", "content": "hi"}],
                "project_id": project["id"], "conversation_id": conversation_id,
            },
            headers=headers,
        )

        detail = await client.get(f"/v1/conversations/{conversation_id}?project_id={project['id']}", headers=headers)
        assert detail.status_code == 200
        messages = detail.json()["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
    clear_overrides()


async def test_delete_conversation(db_session):
    async with make_client(db_session) as client:
        headers = await register_and_login(client, "heidi@example.com")
        project = (await client.post("/v1/projects", json={"name": "Heidi Project"}, headers=headers)).json()
        conv = await client.post(f"/v1/conversations?project_id={project['id']}", json={}, headers=headers)
        conversation_id = conv.json()["id"]

        del_resp = await client.delete(f"/v1/conversations/{conversation_id}?project_id={project['id']}", headers=headers)
        assert del_resp.status_code == 204

        get_resp = await client.get(f"/v1/conversations/{conversation_id}?project_id={project['id']}", headers=headers)
        assert get_resp.status_code == 404
    clear_overrides()
