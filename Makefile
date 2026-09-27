.DEFAULT_GOAL := help
.PHONY: help setup up down db dev migrate migration rollback test lint format openapi

help: ## Show available commands
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  make %-10s %s\n", $$1, $$2}'

setup: ## Install dependencies and create .env
	uv sync
	@test -f .env || cp .env.example .env

up: ## Run the whole app in Docker (API + PostgreSQL)
	docker compose up --build

down: ## Stop Docker containers
	docker compose down

db: ## Start only PostgreSQL in the background
	docker compose up -d --wait db

dev: ## Run the API locally with auto-reload
	uv run fastapi dev app/main.py

migrate: ## Apply database migrations
	uv run alembic upgrade head

migration: ## Create a migration from model changes: make migration m="add field"
	$(if $(m),,$(error Usage: make migration m="describe change"))
	uv run alembic revision --autogenerate -m "$(m)"

rollback: ## Roll back the last migration
	uv run alembic downgrade -1

test: ## Run tests with coverage
	uv run pytest --cov

lint: ## Check code style
	uv run ruff check .
	uv run ruff format --check .

format: ## Fix code style
	uv run ruff check --fix .
	uv run ruff format .

openapi: ## Export openapi.json for the frontend
	uv run python -m scripts.export_openapi
