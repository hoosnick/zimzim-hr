# Makefile for ZIM Attendance Docker Management

.PHONY: help build up down restart logs clean migrate backup restore

# Default target
help:
	@echo "Available commands:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make migrate     - Run database migrations"
	@echo "  make clean       - Remove containers and images (keeps volumes)"
	@echo "  make backup      - Backup PostgreSQL database"
	@echo "  make restore     - Restore PostgreSQL database"
	@echo "  make dev         - Start in development mode"
	@echo "  make prod        - Start in production mode"

# Build images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

# Development mode
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production mode
prod:
	docker-compose up -d

# Run database migrations
migrate:
	docker-compose exec app piccolo migrations forwards all

# Clean containers and images (preserves volumes)
clean:
	docker-compose down --rmi local

# Backup database
backup:
	@echo "Creating database backup..."
	docker-compose exec -T postgres pg_dump -U postgres zim_attendance_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created successfully"

# Restore database (use: make restore FILE=backup_20260123_120000.sql)
restore:
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore FILE=backup_file.sql"; exit 1; fi
	@echo "Restoring database from $(FILE)..."
	docker-compose exec -T postgres psql -U postgres zim_attendance_db < $(FILE)
	@echo "Database restored successfully"

# View app logs
logs-app:
	docker-compose logs -f app

# View worker logs
logs-worker:
	docker-compose logs -f worker

# View poller logs
logs-poller:
	docker-compose logs -f poller

# Shell into app container
shell:
	docker-compose exec app /bin/bash

# Database shell
db-shell:
	docker-compose exec postgres psql -U postgres zim_attendance_db

# Redis CLI
redis-cli:
	docker-compose exec redis redis-cli
