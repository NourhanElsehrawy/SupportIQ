.PHONY: install format-check test lint typecheck migrate migrate-down run up down
install:
	python -m pip install -e ".[dev]"
format-check:
	ruff format --check .
test:
	pytest -q
lint:
	ruff check .
typecheck:
	mypy app tests
migrate:
	alembic upgrade head
migrate-down:
	alembic downgrade -1
run:
	uvicorn app.main:app --reload
up:
	docker compose up --build
down:
	docker compose down
