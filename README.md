# Application Registry

A small internal service that keeps a catalog of the company's applications:
who owns them, where the code lives, and whether they're still in use.

- **Humans** use the web UI: a table of all registered apps and a form to register new ones.
- **Agents and automation** use the REST API (`/api/v1`), described by an OpenAPI spec at
  `/openapi.json` with interactive docs at `/docs`.

Stack: Python 3.12, FastAPI, SQLAlchemy, Jinja2 templates, Postgres (SQLite locally).

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
# open http://localhost:8000
```

Or run a production-like stack with Postgres:

```bash
docker compose up --build
```

## Test and lint

```bash
pytest
ruff check . && ruff format --check .
```

## API quick reference

| Method | Path                           | Purpose                  |
|--------|--------------------------------|--------------------------|
| GET    | `/api/v1/applications`         | List all applications    |
| GET    | `/api/v1/applications/{name}`  | Get one application      |
| POST   | `/api/v1/applications`         | Register an application  |
| GET    | `/healthz`, `/readyz`          | Liveness and readiness   |

Example call from an agent or script:

```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Authorization: Bearer dev-token-change-me" \
  -H "Content-Type: application/json" \
  -d '{"name":"payments-api","owner_team":"Payments","owner_email":"payments@example.com"}'
```

## Configuration

All settings are environment variables with the `APP_` prefix (see `.env.example`):

| Variable                   | Meaning                                                          |
|----------------------------|------------------------------------------------------------------|
| `APP_DATABASE_URL`         | SQLAlchemy URL. `postgresql+psycopg://...` in real environments  |
| `APP_API_TOKENS`           | `name:token,name2:token2` for service accounts and agents         |
| `APP_TRUSTED_USER_HEADER`  | Header set by the SSO proxy with the user's email                |
| `APP_REQUIRE_AUTH`         | `true` in every deployed environment                             |
| `APP_ENVIRONMENT`          | Label shown by `/readyz`                                         |

## Project layout

```
app/                 FastAPI app: API routes, web routes, models, templates
tests/               pytest suite (API + web)
Dockerfile           Multi-stage, non-root production image
docker-compose.yml   Local app + Postgres
deploy/k8s/          Kustomize base + staging/production overlays
.github/workflows/   CI (lint, test, container smoke test) and CD (build, deploy)
docs/                How it's deployed, and the development workflow
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for how this runs in a corporate setting and
[docs/WORKFLOW.md](docs/WORKFLOW.md) for the change → PR → test → deploy pipeline.
