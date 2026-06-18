.PHONY: help up down build test migrate lint format clean

SERVICES := notification-service email-service sms-service push-notification-service \
            in-app-notification-service websocket-service whatsapp-service whatsapp-webjs-service

help:
	@echo "Clan Communication Platform — Development Commands"
	@echo ""
	@echo "  make up            Start all services (Docker Compose)"
	@echo "  make down          Stop all services"
	@echo "  make build         Build all Docker images"
	@echo "  make test          Run all Python tests"
	@echo "  make migrate       Run Alembic migrations for all services"
	@echo "  make lint          Run ruff linter on all Python services"
	@echo "  make format        Run ruff formatter on all Python services"
	@echo "  make logs SERVICE= Stream logs for a specific service"
	@echo "  make shell SERVICE= Open a shell in a running container"
	@echo "  make clean         Remove containers, volumes, and build artifacts"

up:
	docker compose up -d --remove-orphans

down:
	docker compose down

build:
	docker compose build --parallel

logs:
	docker compose logs -f $(SERVICE)

shell:
	docker compose exec $(SERVICE) /bin/bash

test:
	@echo "Running email-service tests..."
	cd services/email-service && python -m pytest tests/ -v --tb=short
	@echo "Running notification-service tests (if any)..."
	@if [ -d services/notification-service/tests ]; then \
		cd services/notification-service && python -m pytest tests/ -v --tb=short; \
	fi

migrate:
	@echo "Running migrations for notification-service..."
	docker compose exec notification-service alembic upgrade head
	@echo "Migrations complete."

lint:
	ruff check libs/ services/

format:
	ruff format libs/ services/

clean:
	docker compose down -v --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Individual service targets
$(addprefix start-,$(SERVICES)):
	docker compose up -d $(@:start-%=%)

$(addprefix stop-,$(SERVICES)):
	docker compose stop $(@:stop-%=%)

$(addprefix restart-,$(SERVICES)):
	docker compose restart $(@:restart-%=%)
