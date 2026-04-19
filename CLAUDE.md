# BeeScout — Claude Code Guardrails

## Project Overview

BeeScout is a **Data Contract Management System** (DCMS) built on the [Open Data Contract Standard (ODCS)](https://github.com/bitol-io/open-data-contract-standard). It lets data teams author, version, and govern data contracts between producers and consumers.

**Stack:**
| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) + MongoDB (Motor async driver) |
| Admin Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| User Frontend | Next.js 15 (App Router), same stack |
| Reverse Proxy | nginx (envsubst template, rate limiting, security headers) |
| Container | Docker Compose (single `make up` workflow) |

---

## Repository Layout

```
beescout/
├── repository/app/         # FastAPI backend
│   ├── core/               # DB connection, JWT, hashing, verification
│   ├── model/              # Pydantic models (metadata.py, model.py, users.py, …)
│   ├── info/               # App metadata (title, version, contact)
│   └── main.py             # All routes (single file by design)
├── frontend-admin/         # Admin UI — roles: admin, root
│   └── src/
│       ├── app/(protected)/contracts/  # Contract CRUD pages
│       ├── lib/api/        # Axios API client
│       └── types/          # Shared TS types + constants
├── frontend-user/          # User UI — roles: user, developer
├── nginx/                  # nginx Dockerfile + envsubst config template
├── data-contract/examples/ # Reference YAML examples (full.yaml is canonical)
├── docker-compose.yml      # Production orchestrator
├── docker-compose.dev.yml  # Dev overlay (exposes ports, hot reload)
└── Makefile                # Developer workflow entrypoint
```

---

## Quick Start

```bash
# 1. Clone and copy env files
make setup        # copies .env.example → .env
make setup-be     # copies repository/app/.env.example → repository/app/.env

# 2. Edit both .env files with real values (domains, secrets, passwords)

# 3. Add local DNS (first run only)
# /etc/hosts: 127.0.0.1 app.localhost admin.localhost

# 4. Run
make up           # build + start all services (production mode)
make dev          # dev mode: ports exposed, hot reload
```

**Ports (production):** Everything is behind nginx on port 80. No service ports exposed directly.

**Ports (dev):** backend → `8888`, frontend-admin → `3001`, frontend-user → `3000`.

---

## Environment Variables

Two separate `.env` files are required:

| File | Used by |
|---|---|
| `.env` (root) | docker-compose: nginx domains, rate limits, MongoDB creds, JWT secrets |
| `repository/app/.env` | FastAPI container at runtime: same secrets in decouple format |

Both must be consistent. `make setup` / `make setup-be` create them from examples.

**Critical values to change before first run:**
- `MONGODB_PASS` — default is `changeme`
- `TKN_SECRET_KEY`, `TKN_SECRET_TOKEN`, `SA_SECRET_KEY`, `SA_SECRET_TOKEN` — generate with `openssl rand -hex 32`
- `BEESCOUT_USER_DOMAIN`, `BEESCOUT_ADMIN_DOMAIN` — your actual subdomains
- `ALLOWED_ORIGINS` — must match your domains exactly
- `COOKIE_SECURE=false` only for local dev without HTTPS

---

## Data Contract Schema

The canonical schema is in `data-contract/examples/full.yaml`. All Pydantic models in `repository/app/model/` must match it.

**Key structure:**
```yaml
standard_version: 0.0.0
contract_number: <generated>
metadata:
  version: 1.0.0
  type: CSV               # file format / system type
  name: ...
  owner: ...
  sla:
    retention: 1          # int (not string)
    retention_unit: tahun # str: tahun | bulan | pekan | hari | jam
  quality:                # dataset-level quality rules
    - code: QR001
      dimension: completeness
      custom_properties:
        - property: threshold
          value: "0.95"
model:                    # column definitions
  - column: id
    logical_type: UUID    # human-readable (Tipe Data Bisnis)
    physical_type: VARCHAR(36)  # SQL type (Tipe Data Teknis)
    quality:              # column-level quality rules (same structure as dataset quality)
      - code: QR002
        dimension: validity
        custom_properties:
          - property: length
            value: "36"
```

**Quality dimensions:** `completeness`, `validity`, `accuracy`

**Stakeholder roles:** `owner`, `consumer`, `steward`, `producer`, `engineer`, `analyst`, `architect`

---

## Backend Conventions

- **All routes in `main.py`** — no router split by design (small surface area)
- **Pydantic models** in `repository/app/model/` — always check these before adding fields to the frontend form
- **`retention`** is stored as `int` + separate `retention_unit: str` — never send as combined string
- **JWT tokens** live in httpOnly cookies — no localStorage auth
- **Access token expiry:** `TKN_ACCESS_TOKEN_EXPIRE_MINUTES=180` (3 hours)
- **MongoDB collections:** `dgr` (contracts), `dgrusr` (users) — configured via env

---

## Frontend Conventions

### React Hook Form — Nested Arrays

**Do NOT use `useFieldArray` with a dynamic `name` string** (e.g., inside a `.map()` callback):

```tsx
// WRONG — crashes when parent array index shifts on delete
useFieldArray({ name: `model.${i}.quality` })

// CORRECT — use watch + setValue for nested dynamic arrays
const rules = form.watch(`model.${columnIndex}.quality`) ?? []
const addRule = () => form.setValue(`model.${columnIndex}.quality`, [...rules, newItem])
```

Use `useFieldArray` only for top-level arrays with stable names (`metadata.stakeholders`, `model`, `ports`).

### Error Handling — FastAPI 422

FastAPI 422 Unprocessable Content returns `detail` as an **array**, not a string:

```ts
// WRONG — React error #31 if detail is an array
toast.error(error.response.data.detail)

// CORRECT — always stringify
const detail = (err as any)?.response?.data?.detail
let msg = 'Gagal menyimpan.'
if (typeof detail === 'string') msg = detail
else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
toast.error(msg)
```

Apply this pattern in **all** form submit handlers.

### API Client

`frontend-admin/src/lib/api/` — Axios instance with:
- Base URL from `NEXT_PUBLIC_API_BASE` (env)
- `withCredentials: true` (cookie-based auth)
- Interceptor: on 401 → calls logout API → redirects to `/login` (avoids infinite loop)

### Auth Flow

- Login sets httpOnly cookie via backend
- Next.js middleware checks cookie presence + JWT format before allowing protected routes
- Malformed cookies are cleared at middleware level

---

## Common Troubleshooting

### MongoDB won't start (WiredTiger crash)

Symptom: container exits immediately, logs say `No space left on device` or `WiredTiger dirty`.

Cause: Docker Desktop VM disk is full (not Mac host disk).

```bash
# 1. Free Docker VM disk space
docker system prune -f && docker builder prune -f

# 2. Repair WiredTiger after unclean shutdown
docker compose run --rm --entrypoint "mongod --repair --dbpath /data/db" db

# 3. Start normally
docker compose up -d db
```

Run `docker system prune -f` periodically on active projects.

### Frontend build fails (TypeScript)

- Variable declaration order matters: destructure `watch`/`setValue` from `form` **before** any call sites (including before `useFieldArray` hooks if `watch` is used in initializers)
- Run `docker compose build frontend-admin` to validate — TypeScript errors appear in build output

### Dev mode hot reload not working

Dev mode (`make dev`) mounts source directories as volumes and runs `next dev`. The `NEXT_PUBLIC_API_BASE` in dev overlay points to `http://localhost:8888` directly. Ensure the backend port is exposed (`docker-compose.dev.yml`).

---

## Access Levels

| Role | Can access | Frontend |
|---|---|---|
| `root` | Everything, including user management | Admin |
| `admin` | Contract CRUD, user management (except root) | Admin |
| `developer` | Read contracts | User |
| `user` | Read contracts (own domain only) | User |

---

## Bootstrap / First-Run Setup

`/setup` (POST) creates the first root account when no root user exists yet. Returns `409` immediately after — effectively self-disabling. `/setup/status` (GET) shows whether setup is done. Never call `/user/create` for the first root account — it requires an existing root token.

## Testing

```bash
make test           # all tests
make test-backend   # pytest (repository/tests/)
make test-fe-admin  # tsc --noEmit
make test-fe-user   # tsc --noEmit
```

Tests use `httpx.AsyncClient` + `unittest.mock` — no real MongoDB needed. All new routes should have a corresponding test in `repository/tests/`.

## Data Contract Schema Versioning

`standard_version` in the YAML tracks the ODCS spec version — do not bump this without reading the upstream ODCS changelog.

For the `metadata.version` field (the contract's own version):
- **Patch** (e.g. `1.0.0 → 1.0.1`): correction to existing field description or constraints
- **Minor** (e.g. `1.0.0 → 1.1.0`): new optional fields added, backward-compatible
- **Major** (e.g. `1.0.0 → 2.0.0`): breaking change — field renamed, required field added, type changed

If a Pydantic model change would break existing saved contracts (stored as MongoDB documents), it is a **major** version change and requires a migration script.

## Making Changes

- **Backend model change** → update Pydantic in `repository/app/model/` + update frontend TypeScript types in `frontend-admin/src/types/` + verify against `data-contract/examples/full.yaml`
- **New frontend page** → add under `src/app/(protected)/` for auth-gated pages, `src/app/(public)/` for open pages
- **nginx routing change** → edit `nginx/templates/default.conf.template` (uses envsubst — use `${VAR}` syntax, not `$var`)
- **Rebuild after change** → `docker compose build <service> && docker compose up -d <service>`
