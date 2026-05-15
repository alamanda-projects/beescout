# =======================
# Project : BeeScout
# File    : Makefile
# Function: Build, run, and manage all components
#
# Quick start (full stack):
#   make setup          — copy .env.example → .env (edit before first run)
#   make up             — build & start all services
#   make down           — stop all services
#
# Development:
#   make dev            — start in dev mode (ports exposed, hot reload)
#   make dev-down       — stop dev stack
#
# Backend only (standalone):
#   make up-be          — start backend + db only
# =======================

MONGODB_USER ?= admin
MONGODB_PASS ?= changeme


# ── Environment setup ──────────────────────────────────────────────────────────

setup:
	@if [ -f .env ]; then \
		echo ".env already exists, skipping."; \
	else \
		cp .env.example .env; \
		echo ".env created — edit it with your values before running 'make up'"; \
	fi


# ── Full stack (production) ────────────────────────────────────────────────────

up:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

status:
	docker compose ps


# ── Development mode ───────────────────────────────────────────────────────────

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

dev-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

dev-logs:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f


# ── Backend standalone (no frontend, no nginx) ────────────────────────────────

up-be:
	docker compose up --build -d backend db

down-be:
	docker compose stop backend db


# ── Individual image builds ────────────────────────────────────────────────────

build-backend-arm64:
	docker build \
		-f repository/infra/python/Dockerfile \
		--platform linux/arm64 \
		-t beescout-backend:latest-arm64 .

build-backend-amd64:
	docker build \
		-f repository/infra/python/Dockerfile \
		--platform linux/amd64 \
		-t beescout-backend:latest-amd64 .

build-db-arm64:
	docker build \
		-f repository/infra/mongodb/Dockerfile \
		--build-arg MONGODB_USER=$(MONGODB_USER) \
		--build-arg MONGODB_PASS=$(MONGODB_PASS) \
		--platform linux/arm64 \
		-t beescout-db:latest-arm64 .

build-db-amd64:
	docker build \
		-f repository/infra/mongodb/Dockerfile \
		--build-arg MONGODB_USER=$(MONGODB_USER) \
		--build-arg MONGODB_PASS=$(MONGODB_PASS) \
		--platform linux/amd64 \
		-t beescout-db:latest-amd64 .

build-nginx:
	docker build \
		-f nginx/Dockerfile \
		-t beescout-nginx:latest \
		nginx/

build-fe-user:
	docker build \
		-f frontend-user/Dockerfile \
		-t beescout-fe-user:latest \
		frontend-user/

build-fe-admin:
	docker build \
		-f frontend-admin/Dockerfile \
		-t beescout-fe-admin:latest \
		frontend-admin/


# ── Testing ───────────────────────────────────────────────────────────────────

test-backend:
	cd repository && pip install pytest pytest-asyncio httpx --quiet && pytest tests/ -v

test-fe-admin:
	cd frontend-admin && npx tsc --noEmit

test-fe-user:
	cd frontend-user && npx tsc --noEmit

test: test-backend test-fe-admin test-fe-user
	@echo "All tests passed."


# ── Utilities ──────────────────────────────────────────────────────────────────

clean:
	docker image prune -f

clean-all:
	docker compose down -v --rmi local
	docker image prune -f

health:
	@curl -sf http://localhost:8888/health | python3 -m json.tool || echo "Backend not reachable"


# ── Legacy targets (kept for backward compatibility) ──────────────────────────

docker_build_app_arm64: build-backend-arm64
docker_build_app_amd64: build-backend-amd64
docker_build_db_arm64:  build-db-arm64
docker_build_db_amd64:  build-db-amd64
docker_compose_up:      up
docker_remove_dangling_images: clean
service_stop:           down-be
copy_env_file:          setup
