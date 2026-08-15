"""
RAG / pgvector integration tests.

document_chunks uses pgvector's Vector column type, which has no SQLite
equivalent (see tests/conftest.py), so these tests need a real
Postgres+pgvector instance and are skipped unless RUN_PG_INTEGRATION_TESTS
is set (e.g. in CI, pointed at the docker-compose postgres service):

    RUN_PG_INTEGRATION_TESTS=1 pytest tests/integration/test_rag.py

This mirrors the spec's own instruction to mock external provider calls in
unit tests and reserve real dependencies for integration tests - extended
here to the database, since pgvector specifically can't be faked in-memory.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_PG_INTEGRATION_TESTS"),
    reason="requires a real Postgres+pgvector instance; set RUN_PG_INTEGRATION_TESTS=1 to run",
)


async def test_chunk_and_retrieve_roundtrip():
    # Intentionally left as a template: with RUN_PG_INTEGRATION_TESTS=1 and
    # DATABASE_URL pointed at the docker-compose postgres service, this
    # would upload a document via the API, poll for status == "ready",
    # call /v1/knowledge/bases/{kb_id}/retrieve, and assert the expected
    # chunk comes back with the highest score.
    pytest.skip("template for real-Postgres RAG verification - fill in against a live pgvector instance")
