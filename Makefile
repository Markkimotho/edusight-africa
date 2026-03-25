# EduSight Africa — Project Makefile
#
# Prerequisites: Docker, Docker Compose v2
#
# Usage:
#   make up          Start all services in detached mode
#   make down        Stop all services
#   make logs        Follow logs for all services
#   make build       Build (or rebuild) all Docker images
#   make clean       Stop services and remove volumes (destructive)
#   make migrate     Run Alembic database migrations
#   make seed        Seed the database with initial data
#   make test-backend Run pytest suite inside the backend container
#   make backend-shell Open an interactive shell in the backend container

COMPOSE        = docker compose
BACKEND_CTR    = edusight_backend
FRONTEND_CTR   = edusight_frontend

.PHONY: up down logs build clean migrate seed test-backend backend-shell help

## ─── Lifecycle ──────────────────────────────────────────────────────────────

up: ## Start all services in detached mode
	$(COMPOSE) up -d

down: ## Stop all running services
	$(COMPOSE) down

logs: ## Follow aggregated logs for all services
	$(COMPOSE) logs -f

build: ## Build (or rebuild) all Docker images
	$(COMPOSE) build

clean: ## Stop services and remove all volumes (WARNING: deletes DB data)
	$(COMPOSE) down -v

## ─── Database ────────────────────────────────────────────────────────────────

migrate: ## Run Alembic migrations inside the backend container
	$(COMPOSE) exec $(BACKEND_CTR) alembic upgrade head

seed: ## Seed the database with initial / demo data
	$(COMPOSE) exec $(BACKEND_CTR) python scripts/seed.py

## ─── Testing ─────────────────────────────────────────────────────────────────

test-backend: ## Run pytest with coverage inside the backend container
	$(COMPOSE) exec $(BACKEND_CTR) pytest tests/ -v --cov=app --cov-report=term-missing

## ─── Shells ──────────────────────────────────────────────────────────────────

backend-shell: ## Open an interactive bash shell inside the backend container
	$(COMPOSE) exec $(BACKEND_CTR) /bin/bash

## ─── Help ────────────────────────────────────────────────────────────────────

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
