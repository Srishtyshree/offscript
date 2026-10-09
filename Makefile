.DEFAULT_GOAL := help
.PHONY: help install dev dev-api dev-web health smoke-test test test-py test-web lint format

API_PORT ?= 8000

help: ## List commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

install: ## Install all Python (uv) and web (npm) dependencies + git hooks
	uv sync --all-packages
	cd web && npm ci
	uv run pre-commit install

dev: ## Run API and web together
	$(MAKE) -j2 dev-api dev-web

dev-api: ## Run the API with reload on :$(API_PORT)
	cd api && uv run uvicorn offscript_api.main:app --reload --port $(API_PORT)

dev-web: ## Run the web dev server on :5173
	cd web && npm run dev

health: ## Check the running API's /health
	curl -fsS http://localhost:$(API_PORT)/health && echo

smoke-test: ## Live Tinker check: sample, tiny train, save (needs training/.env, costs cents)
	uv run --env-file training/.env python -m offscript_training.smoke_test

test: test-py test-web ## Run all tests

test-py:
	uv run pytest api contract training

test-web:
	cd web && npm test

lint: ## Lint + format check + type check
	uv run ruff check .
	uv run ruff format --check .
	cd web && npm run lint && npm run format:check && npm run typecheck

format: ## Auto-format Python and web
	uv run ruff check --fix .
	uv run ruff format .
	cd web && npm run format
