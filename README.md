# SupportIQ

A production-style enterprise AI support platform built to demonstrate AI engineering, backend engineering, DevOps, MLOps and LLMOps.

## Current milestone: Persistent application foundation

This starter includes:

- FastAPI application with a health endpoint
- SQLAlchemy 2.x engine and request-scoped sessions
- Minimal persistent User model
- Alembic schema migrations
- PostgreSQL readiness endpoint
- PostgreSQL 17 with pgvector
- Redis
- Multi-stage, non-root Docker image
- Docker Compose with health checks
- Pytest, Ruff and strict mypy configuration
- GitHub Actions CI for quality checks and image builds
- Terraform development-environment scaffold
- First architecture decision record

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

Apply database migrations in another terminal:

```bash
docker compose run --rm api alembic upgrade head
```

Open:

- API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Readiness: http://localhost:8000/health/ready

## Run without Docker

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
pytest -q
uvicorn app.main:app --reload
```

Run PostgreSQL integration tests by setting `TEST_DATABASE_URL` to a dedicated
test database before running pytest. Integration tests are skipped when it is
not set.

## Roadmap

1. Foundation and engineering standards
2. Database models, migrations and authentication
3. Document ingestion and object storage
4. Embeddings, pgvector and retrieval
5. Grounded chat with citations
6. Tool calling and background jobs
7. Evaluation datasets and CI quality gates
8. Tracing, metrics and dashboards
9. Terraform AWS infrastructure
10. Staging deployment and continuous delivery
