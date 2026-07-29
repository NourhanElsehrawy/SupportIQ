# ADR 0001: Start with a modular monolith and container-first development

## Status
Accepted

## Context
SupportIQ needs production-style engineering practices without premature distributed-system complexity.

## Decision
Use a modular FastAPI application, PostgreSQL/pgvector, Redis and background workers in one repository. Each deployable component receives its own container image when introduced.

## Consequences
- Fast local development and simple debugging.
- Clear module boundaries can later become services.
- CI, observability and evaluation are introduced before feature complexity grows.
