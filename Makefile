# =======================
# Project : BeeScout
# File    : Makefile
# Function: Build, run, and manage all components
#
# Quick start (full stack):
#   cp .env.example .env
#   make up             — build & start all services
#   make down           — stop all services
#
# Development:
#   make dev            — start in dev mode (ports exposed, hot reload)
#   make dev-down       — stop dev stack
#
# Database:
#   make reset-db       — wipe production DB volume & re-init (DESTRUCTIVE)
#   make dev-reset-db   — wipe dev DB volume & re-init (DESTRUCTIVE)
#
# Housekeeping:
#   make prune          — hapus dangling image + build cache (free disk)
#
# DB access dari Mac:
#   make db-expose      — expose MongoDB :27017 ke localhost (Compass/TablePlus)
#   make db-hide        — kembalikan ke mode production (port ditutup)
#
# Backend only (standalone):
#   make up-be          — start backend + db only
# =======================

# ⚠️ PLACEHOLDER — WAJIB diganti di production!
# Nilai default ini hanya untuk target build standalone (build-db-*).
# Untuk pemakaian normal via docker compose, kredensial dibaca dari .env.
# Override saat build: make build-db-amd64 MONGODB_USER=xxx MONGODB_PASS=yyy
MONGODB_USER ?= admin
MONGODB_PASS ?= changeme


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

# Wipe production DB: hapus volume data, MongoDB re-init dari awal saat start.
reset-db:
	@echo "⚠️  Ini MENGHAPUS SEMUA DATA database produksi (volume beescout_beescout-data)."
	@read -p "Lanjutkan? [y/N] " ans; [ "$$ans" = "y" ] || { echo "Dibatalkan."; exit 1; }
	docker compose stop db
	docker compose rm -f db
	docker volume rm -f beescout_beescout-data
	docker compose up -d db
	@echo "✓ Database produksi di-reset. MongoDB re-init dari awal."


# ── DB access dari Mac host (untuk Compass, TablePlus, dll.) ─────────────────
# Pakai docker-compose.local.yml (gitignored). Port 27017 di-bind ke 127.0.0.1
# saja (loopback). Koneksi: localhost:27017, user=admin, authDB=admin.
# File override dibuat otomatis dari .example bila belum ada.

db-expose:
	@test -f docker-compose.local.yml || { \
		cp docker-compose.local.yml.example docker-compose.local.yml; \
		echo "→ docker-compose.local.yml dibuat dari .example"; \
	}
	docker compose -f docker-compose.yml -f docker-compose.local.yml up -d db
	@echo "✓ MongoDB tersedia di localhost:27017 (auth: admin / MONGODB_PASS dari .env, authSource=admin)"

db-hide:
	docker compose up -d db
	@echo "✓ MongoDB kembali ke mode production (port tidak di-expose ke host)"

# ── Development mode ───────────────────────────────────────────────────────────

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

dev-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

dev-logs:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Wipe dev DB: hapus volume data dev, MongoDB re-init dari awal saat start.
dev-reset-db:
	@echo "⚠️  Ini MENGHAPUS SEMUA DATA database dev (volume beescout_beescout-dev-data)."
	@read -p "Lanjutkan? [y/N] " ans; [ "$$ans" = "y" ] || { echo "Dibatalkan."; exit 1; }
	docker compose -f docker-compose.yml -f docker-compose.dev.yml stop db
	docker compose -f docker-compose.yml -f docker-compose.dev.yml rm -f db
	docker volume rm -f beescout_beescout-dev-data
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
	@echo "✓ Database dev di-reset. MongoDB re-init dari awal."


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


# ── API documentation ─────────────────────────────────────────────────────────

# Regenerate docs/api/beescout.postman_collection.json dari skema OpenAPI
# FastAPI. Wajib dijalankan setiap kali ada perubahan endpoint (CLAUDE.md DoD).
# Mount source app + scripts + docs ke container backend; tidak menyentuh DB.
regen-postman:
	docker compose run --rm --user root \
		-v $(PWD)/repository/app:/work/app \
		-v $(PWD)/repository/scripts:/work/scripts \
		-v $(PWD)/docs:/work/docs \
		backend python -m scripts.gen_postman


# ── Migration & maintenance scripts ───────────────────────────────────────────
#
# `scripts/` sengaja tidak masuk production image (Dockerfile hanya copy
# `app/`). Untuk menjalankan migration / break-glass script, mount script
# dir + app dir ke container backend yang sudah jalan.
#
# Set APPLY=1 untuk eksekusi (default: dry-run).
# Contoh: make migrate-stakeholder-roles APPLY=1

# Argumen tambahan akan jadi `--apply` bila APPLY=1, sisanya kosong.
APPLY_FLAG := $(if $(APPLY),--apply,)

# Internal helper — pakai oleh target migrate-* di bawah.
define _run_script
	docker compose run --rm --user root \
		-v $(PWD)/repository/app:/work/app \
		-v $(PWD)/repository/scripts:/work/scripts \
		backend python -m scripts.$(1) $(APPLY_FLAG)
endef

# Strict stakeholder.role ke 4 nilai spec BeeScout (PR #112 / strict role).
migrate-stakeholder-roles:
	$(call _run_script,migrate_stakeholder_roles)

# Backfill stakeholders[] dari metadata.consumer[] legacy (PR #105 / ADR-0007 Phase 2).
migrate-consumer-to-stakeholders:
	$(call _run_script,migrate_consumer_to_stakeholders)

# Pindah effective_date / expiry_date ke metadata top-level (#103 / standard 0.5.0).
migrate-period-to-toplevel:
	$(call _run_script,migrate_period_to_toplevel)

# Backfill model[].description kosong dengan penanda dari nama (#102 PR-B slice 4).
migrate-backfill-model-description:
	$(call _run_script,migrate_backfill_model_description)

# Backfill approvers_by_role di approval lama (PR #70 / ADR-0004).
migrate-approval-roles:
	$(call _run_script,migrate_approval_roles)

# Migrate quality impact value lama (low/medium/high) ke impact + severity (ADR-0003).
migrate-impact-severity:
	$(call _run_script,migrate_impact_severity)

# Dedup kontrak duplikat (DuplicateKeyError fix di unique contract_number index).
dedupe-contracts:
	$(call _run_script,dedupe_contracts)

# Break-glass root account recovery (sengaja tanpa default — wajib pass arg).
# Contoh: make recover-root ARGS="--username root --name 'Root User' --apply"
recover-root:
	docker compose run --rm --user root \
		-v $(PWD)/repository/app:/work/app \
		-v $(PWD)/repository/scripts:/work/scripts \
		backend python -m scripts.recover_root $(ARGS)


# ── Utilities ──────────────────────────────────────────────────────────────────

clean:
	docker image prune -f

# Housekeeping disk: hapus dangling image + build cache yang tak terpakai.
# Aman — hanya menghapus yang tidak direferensikan container/image aktif.
# Jalankan berkala bila `docker system df` menunjukkan akumulasi (issue #20).
prune:
	docker image prune -f
	docker builder prune -f
	@echo "── docker system df ──"
	@docker system df

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
