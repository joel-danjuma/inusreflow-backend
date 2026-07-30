.PHONY: up down migrate test lint typecheck format rbac-matrix

up:
	docker compose up -d

down:
	docker compose down

migrate:
	uv run alembic upgrade head

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy app

rbac-matrix:
	uv run python -m scripts.generate_rbac_matrix
