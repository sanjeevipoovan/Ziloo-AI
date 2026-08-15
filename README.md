# MyAI Backend (V1)

A production-oriented modular monolith for a multi-model AI platform. FastAPI
in front, Hugging Face-hosted GLM-5.2 and Kimi K3 behind a provider
abstraction, PostgreSQL + pgvector for storage and RAG, Redis for rate
limiting.

```
Client -> FastAPI -> Orchestrator -> Model Router -> Provider (Hugging Face) -> GLM-5.2 / Kimi K3
                         |                                        |
                         +-- Context Builder (prompt assembly)    +-- normalized into ProviderResponse
                         v
                    PostgreSQL / pgvector, Redis, Sentry
```

## Two design principles this build was built around

**No hardcoding.** Nothing outside `app/providers/huggingface.py` knows
Hugging Face exists, and even that file only knows whatever `model_identifier`
and token it's handed at call time. The chain is:

```
LLMProvider (interface, app/providers/base.py)
    -> HuggingFaceProvider (app/providers/huggingface.py)
Model Registry (DB-backed, app/models/registry.py)
    -> rows seeded from GLM_MODEL_ID / KIMI_MODEL_ID env vars (app/db/seed.py)
Model Router (app/models/router.py)
    -> deterministic auto-routing policy, independent of the API layer
```

Adding vLLM, OpenAI, Anthropic, or a future self-hosted MyAI model means
writing one new class implementing `LLMProvider` and inserting a registry
row - no changes to routing, orchestration, or API code. Swapping which HF
model backs "glm-5.2" is an env var change, not a deploy.

**Better prompting.** Every code path that talks to a model - a direct
chat completion, an agent run, a RAG-grounded query - goes through
`ContextBuilder` (`app/orchestrator/context.py`) to assemble the system
prompt and message list. There's exactly one place that decides how a
system prompt is built, how retrieved context is framed (with explicit
citation instructions and an explicit "say so if you don't know"
instruction), and how conversation history is threaded in - instead of
each route hand-rolling prompt strings.

## Important: this was built without network access

I wrote this in a sandboxed environment with no network access, so I could
not `pip install`, run Docker, connect to a real Postgres/Redis, or call
Hugging Face. Concretely, that means:

- **Verified:** every file's Python syntax (`py_compile`), the overall
  import graph, and the logic by careful review. The Hugging Face client
  usage (`AsyncInferenceClient.chat_completion`) was checked against
  current documentation mid-build rather than assumed from memory.
- **Not verified:** an actual `docker compose up`, a real `alembic upgrade
head` against Postgres, a real `pytest` run, or a real call to GLM-5.2 /
  Kimi K3. The initial migration (`migrations/versions/0001_initial.py`)
  was hand-written to mirror the ORM models exactly, since generating it
  with `alembic revision --autogenerate` requires a live database
  connection I didn't have.

**Recommended next step:** open this project in Claude Code (or your own
terminal) where there's real network access, and run the Quickstart below.
If anything doesn't come up cleanly, that's the fastest way to find and fix
it - Claude Code can install dependencies, run the migration, run the
tests, and iterate against real errors, which this sandbox couldn't do.

## Quickstart

```bash
cp .env.example .env
# edit .env: set JWT_SECRET, HF_API_TOKEN, and confirm GLM_MODEL_ID / KIMI_MODEL_ID

docker compose up --build
```

This builds the API image, starts Postgres (with pgvector) and Redis, runs
`alembic upgrade head` automatically, then starts the API on
`http://localhost:8000`. Interactive docs at `/docs`.

```bash
# 1. Register + log in
curl -X POST localhost:8000/v1/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"supersecret123"}'
TOKEN=$(curl -s -X POST localhost:8000/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"supersecret123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# 2. Create a project
PROJECT_ID=$(curl -s -X POST localhost:8000/v1/projects -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"My Project"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')

# 3. Create an API key (shown once - save it)
curl -X POST localhost:8000/v1/projects/$PROJECT_ID/api-keys -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"local-dev"}'

# 4. Chat, with auto routing
curl -X POST localhost:8000/v1/chat/completions -H "X-API-Key: $MYAI_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"auto","messages":[{"role":"user","content":"Explain RAG in one paragraph"}]}'
```

## Configuration

All settings live in `app/core/config.py` and are read from `.env` /
environment variables (see `.env.example` for the full list with
descriptions). Nothing here is optional except where a default is shown -
`DATABASE_URL`, `JWT_SECRET`, `HF_API_TOKEN`, `GLM_MODEL_ID`, and
`KIMI_MODEL_ID` are required and the app will refuse to start without them.

## Auth model

Two mechanisms, resolved to one `Principal` (`app/api/dependencies.py`):

- **Human users** — JWT bearer token from `/v1/auth/login`. Used for
  dashboard-style access (creating projects, agents, API keys). A JWT isn't
  scoped to a project, so project-scoped endpoints require `project_id`
  explicitly and verify ownership on every call.
- **External applications** — a MyAI API key (`X-API-Key` header, prefix
  `myai_`). Scoped to exactly one project at creation time; every request
  is pinned to that project regardless of what's in the request body.

Every project-scoped resource (agents, conversations, knowledge bases, API
keys) is reachable only through `require_project_access` /
`get_resolved_project_id` - see `tests/security/` for the IDOR tests this
is meant to satisfy.

## Testing

```bash
pip install -r requirements.txt
pytest
```

Most of the suite runs against an in-memory SQLite database
(`tests/conftest.py`) with the Hugging Face provider replaced by
`tests/fakes.py::FakeProvider` (or `FailingProvider`, for the
provider-failure test) - no network needed. One deliberate exception:
**`document_chunks` uses pgvector's `Vector` column type, which has no
SQLite equivalent**, so RAG/vector-search is excluded from the SQLite
fixture and covered instead by `tests/integration/test_rag.py`, gated
behind a real Postgres instance:

```bash
RUN_PG_INTEGRATION_TESTS=1 DATABASE_URL=postgresql+asyncpg://myai:myai@localhost:5432/myai pytest tests/integration/test_rag.py
```

Coverage: registration/login/JWT auth, API-key auth/revocation, project
isolation (IDOR), the model router's routing decisions, the HF provider's
response normalization (mocked), the chat endpoint (incl. streaming and
provider-failure paths), conversation persistence, agent create/run,
and rate limiting.

## Project layout

```
app/
  core/          settings, security (password/JWT/API-key), logging, exceptions
  db/            SQLAlchemy models, session, seed
  schemas/       Pydantic request/response models
  providers/     LLMProvider interface + Hugging Face implementation
  models/        Model Registry + Model Router (business logic, not ORM)
  orchestrator/  Context Builder, Execution Engine, Orchestrator
  rag/           document loader, chunker, embeddings, retriever
  services/      auth, project, api_key, conversation, agent, usage, rate_limit, audit
  middleware/    request ID + access log, rate limiting, security headers
  api/routes/    FastAPI routers
migrations/      Alembic (async)
tests/           unit / integration / security
```

## Known gaps for the next iteration

- API key `scopes` are stored and returned but not yet enforced per-endpoint
  (currently authorization is project-level only, as the spec asks for in
  V1: "do not build complex enterprise RBAC yet").
- Document processing runs via FastAPI `BackgroundTasks`, not a queue - fine
  for V1 per the spec, but move to Celery if upload volume grows.
- Audit logging covers project creation and API key lifecycle; extend
  `AuditService` calls to more mutations as needed.
- The initial migration was hand-written and needs to be checked against a
  real Postgres instance (see "Important" above).
  ||||||| empty tree
  =======

# Ziloo-AI

> > > > > > > 6029a5c081d3ee10e2456495a944185458aaa153
