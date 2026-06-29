.PHONY: install run test lint simulate eval eval-category

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

# Run full evaluation suite against the live server (make run first)
eval:
	uv run python -m tests.eval.runner --output results/eval_report.json

# Run a single category: make eval-category CAT=order_tracking
eval-category:
	uv run python -m tests.eval.runner --category $(CAT)

# Multi-turn simulation: make simulate (SIM-01), make simulate SCENARIO=SIM-04, make simulate-all
simulate:
	uv run python -m tests.simulation --scenario $(or $(SCENARIO),SIM-01) --verbose

simulate-all:
	uv run python -m tests.simulation --all
