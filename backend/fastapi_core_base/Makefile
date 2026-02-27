.PHONY: help sync lint format test run-app run-worker clean pc pc-all bootstrap

# Variables
PYTHON_VERSION := $(shell cat .python-version 2>/dev/null || echo "3.12")
UV := uv
PYTHON := $(UV) run python

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: help sync sync-all lint format fix test run-app run-worker clean deep-clean pc pc-all bootstrap inspect-config list-routes db-shell migrate migrate-create migrate-status

sync: ## Install dependencies and sync .venv
	$(UV) sync

sync-all: ## Install all group dependencies
	$(UV) sync --all-groups

lint: ## Run linting checks (Ruff & Mypy)
	$(UV) run ruff check src tests
	$(UV) run mypy src

format: ## Format code with Ruff
	$(UV) run ruff format src tests

fix: ## Automatically fix linting and formatting issues
	$(UV) run ruff check --fix src tests
	$(UV) run ruff format src tests

test: ## Run tests with coverage
	$(UV) run pytest --cov=src tests/

# --- Pre-commit Aliases ---

pc: ## Run pre-commit on staged files only
	$(UV) run pre-commit run

pc-all: ## Run pre-commit on all files in the repository
	$(UV) run pre-commit run --all-files

# --- Database Migrations (Alembic) ---

migrate: ## Run pending database migrations
	$(UV) run alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create msg="description")
	$(UV) run alembic revision --autogenerate -m "$(msg)"

migrate-status: ## Show current migration status
	$(UV) run alembic current
	$(UV) run alembic history --verbose

# --- Execution ---

run-app: ## Run the FastAPI development server
	$(UV) run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

run-worker: ## Run a local Cloud Run worker
	@echo "Starting Data Worker..."
	$(UV) run python src/cloud_run/data_worker/main.py

# --- Developer Utilities ---

inspect-config: ## Show active Dynaconf settings (debug)
	$(UV) run python -c "from src.shared.configuration.config import settings; import json; print(json.dumps(settings.as_dict(), indent=2, default=str))"

list-routes: ## List all registered FastAPI routes
	$(UV) run python -c "from src.app.main import app; [print(f'{r.methods} {r.path}') for r in app.routes]"

db-shell: ## Open a shell for the local DuckDB database
	$(UV) run duckdb duckdb_data/local.duckdb

# --- Client Specific Helpers ---

run-client-a: ## Run App specifically for Client A
	ENV_FOR_DYNACONF=client_a $(UV) run uvicorn src.app.main:app --reload

# --- Setup & Cleanup ---

bootstrap: sync ## Initial project setup (create folders and install hooks)
	mkdir -p logs duckdb_data
	mkdir -p parquet_data/raw parquet_data/silver parquet_data/gold
	touch logs/app.log duckdb_data/.gitkeep parquet_data/.gitkeep
	$(UV) run pre-commit install
	@echo "Project Bootstrapped! Try running 'make pc-all' to verify hooks."

clean: ## Remove temporary files, caches, and logs
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f logs/*.log

deep-clean: clean ## Remove .venv and lock files for a fresh start
	rm -rf .venv uv.lock