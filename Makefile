# Makefile for FastAPI Quiz Project
# Load environment variables from .env
include .env
export

.PHONY: help build up down test lint format migrate seeder shell db-shell logs clean

# Variables
DOCKER_COMPOSE := docker compose -f docker-compose.yml
SERVICE_NAME := web
DB_SERVICE := db

help:  ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

build: ## Build the Docker containers
	$(DOCKER_COMPOSE) build --no-cache

up: ## Start the containers in detached mode
	$(DOCKER_COMPOSE) up -d

down: ## Stop and remove containers
	$(DOCKER_COMPOSE) down

logs: ## View container logs
	$(DOCKER_COMPOSE) logs -f $(SERVICE_NAME)

test: ## Run pytest with coverage
	$(DOCKER_COMPOSE) run --rm $(SERVICE_NAME) pytest -v --cov=src --cov-report=html

lint: ## Run code quality checks
	$(DOCKER_COMPOSE) run --rm $(SERVICE_NAME) \
		black --check src/ \
		&& flake8 src/ \
		&& isort --check-only src/

format: ## Format the code automatically
	$(DOCKER_COMPOSE) run --rm $(SERVICE_NAME) \
		black src/ \
		&& isort src/

migrate: ## Run database migrations
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) alembic upgrade head

seeder: ## Run database seeder
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python database/run_seeder.py

shell: ## Access container shell
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) /bin/bash

db-shell: ## Access PostgreSQL database shell
	$(DOCKER_COMPOSE) exec $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

clean: ## Remove temporary files and Docker artifacts
	find . -type d -name '__pycache__' -exec rm -rf {} +
	docker system prune -f
	$(DOCKER_COMPOSE) down -v --rmi all
 