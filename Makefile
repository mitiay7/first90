.PHONY: install run test lint check compose-up compose-down

install:
	uv sync

run:
	uv run uvicorn app.main:app --reload --port 8000

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

check: lint test

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down
