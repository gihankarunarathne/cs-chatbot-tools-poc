.PHONY: install run test lint

install:
	uv sync --extra dev

run:
	uv run uvicorn cschatbot.api.app:create_app --factory --reload --port 8080

test:
	uv run pytest -v

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff format src/ tests/
