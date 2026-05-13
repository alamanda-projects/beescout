# BeeScout — Claude Code Guardrails

> This file is the **technical guardrail for AI agents (and developers)** working on this codebase.
> It contains conventions, gotchas, and rules-of-thumb that prevent common mistakes.
> It does **not** explain what BeeScout is or who it's for — see the docs below for that.

## Where to find the rest

| Looking for... | Read this |
|---|---|
| What BeeScout does, stack, repo layout | [README.md](README.md) |
| Local setup & environment variables | [getting-started.md](getting-started.md), [.env.example](.env.example) |
| Who BeeScout is built for (4 personas) | [docs/personas.md](docs/personas.md) |
| Business ↔ technical term mapping | [docs/glossary.md](docs/glossary.md) |
| How to contribute (incl. AI usage policy) | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Who decides what, how to become a maintainer | [GOVERNANCE.md](GOVERNANCE.md) |
| Reporting vulnerabilities | [SECURITY.md](SECURITY.md) |
| Canonical data contract schema | [data-contract/examples/full.yaml](data-contract/examples/full.yaml) |
| Approval workflow, rule catalog, YAML import | [docs/](docs/) |

When you need user-facing personas (Pak Bambang/Bu Retno/Mas Dimas/Mbak Indah), reference `docs/personas.md` rather than re-deriving them.

---

## Working Mode

The maintainer (single, [@haninp](https://github.com/haninp)) operates **brainstorm-heavy** — most input is "ide / fitur / bug report" in Bahasa Indonesia. **Your job is to execute**: investigate the codebase, propose a concrete plan when the task is non-trivial, implement, run QA, and open a PR.

- **Language**: Maintainer writes in Bahasa Indonesia. Reply in the same language. User-facing UI strings are Indonesian (follow [docs/glossary.md](docs/glossary.md)); code identifiers, file names, commit subjects, and PR titles stay in English (conventional-commit style).
- **PR is the unit of delivery** — every change goes through a PR, even one-line fixes. Maintainer reviews & merges from mobile (GitHub mobile app).
- **Issues are the source of truth** for pending work — not chat history, not memory. If a non-trivial decision emerges mid-task, leave a comment on the relevant issue/PR before the chat moves on. Future agents (cloud or local) read issues, not transcripts.
- **`docs/sdlc.md`** is the canonical lifecycle. Skip steps only when the change is truly trivial (typo, comment fix).

### Definition of Done (before opening a PR)

1. **Tests pass locally**: `make test` (backend + both frontend typechecks).
2. **QA scripts pass**: every `scripts/qa-*.sh` relevant to the change exits 0. The form button safety check (`scripts/qa-form-buttons.sh`) runs on every PR via CI — keep it green.
3. **New convention discovered? Document it.** Add a section to this file (and a longer write-up under `docs/` if it deserves one). Future you / future agent will need it.
4. **PR description** includes: short summary, "Closes #N" trailer, test plan checklist.
5. **Branch naming**: `<type>/<issue#>-<slug>` where `type` ∈ `fix | feat | chore | docs | refactor`. Example: `fix/12-unique-contract-number`.
6. **Squash-merge only** (project default). The branch is deleted on merge.

### When the task is non-trivial

Use the plan mode (Claude Code) or write a plan file to `.github/` / comment on the issue **before** writing code. A plan should include: context (why), scope (what), files to touch, risk/trade-offs, and verification approach. Mirror the style of existing plans under `.claude/plans/` if available, or follow [docs/sdlc.md](docs/sdlc.md)'s "Design" step.

---

## Backend Conventions

- **All routes in `repository/app/main.py`** — single-file by design (small surface area). Don't introduce a router split without a [Tech Proposal](.github/ISSUE_TEMPLATE/tech-proposal.yml).
- **Pydantic models in `repository/app/model/`** — always check these before adding fields to the frontend form. Frontend types in `frontend-admin/src/types/` (and mirrored in `frontend-user/`) must stay in sync.
- **`retention`** is stored as `int` + separate `retention_unit: str` (values: `tahun | bulan | pekan | hari | jam`). Never combine into one string.
- **JWT tokens** live in httpOnly cookies — never localStorage. Default access token expiry: 180 minutes (3 hours).
- **MongoDB collections** are configured via env (`MONGODB_COL_*`). Common ones: `dgr` (contracts), `dgrusr` (users), approvals collection (see `core/connection.py`).
- **Role gating dependencies**: use the helpers in `main.py` — `require_root`, `require_admin`, `require_any`. Don't re-implement role checks inline.
- **Endpoint naming**: lowercase + slash-separated noun + verb (e.g., `/datacontract/lists`, `/user/create`, `/approval/{id}/vote`).

### Quick reference: Access Levels

| Role | Frontend | Contract scope | Notes |
|---|---|---|---|
| `root` | Admin | All contracts | Plus user management of non-root |
| `admin` | Admin | All contracts | Acts as steward |
| `developer` | User | Contracts where user's team is in `metadata.consumer[]` | Technical lens (`eng` mode); plus generate SA keys |
| `user` | User | Contracts where user's team is in `metadata.consumer[]` | Business lens (`biz` mode) |

> **Important**: `developer` and `user` share the **same scope** — both see contracts where their team (user's `data_domain`) is listed as a consumer. A team is the unit, containing both technical and business members. They differ in mindset/UI mode, not in access. Cross-team visibility is the steward's (`admin`) responsibility. See [docs/personas.md](docs/personas.md).
>
> Note: `/datacontract/lists` additionally surfaces contracts where the user is `created_by` or in `managers` — this is the "my responsibilities" lens (separate from the consumer-team scope above).

### Bootstrap

`/setup` (POST) creates the first root account when no root user exists. Returns `409` immediately after — effectively self-disabling. `/setup/status` (GET) shows whether setup is done. Never call `/user/create` for the first root account.

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

### Form buttons — `type` is mandatory

Every raw `<button>` used as a non-submit action **must** have an explicit `type="button"`. HTML default for `<button>` inside `<form>` is `type="submit"` — silently triggers form submit on click.

```tsx
// ✗ wrong — clicking this submits the parent form
<button onClick={toggleMode}>Bisnis</button>

// ✓ right
<button type="button" onClick={toggleMode}>Bisnis</button>
```

Shadcn `<Button>` defaults to `type="button"` (defensive default in [frontend-admin/src/components/ui/button.tsx](frontend-admin/src/components/ui/button.tsx)) — submit buttons must be explicit (`<Button type="submit">`). Enforced in CI by [scripts/qa-form-buttons.sh](scripts/qa-form-buttons.sh). See [docs/form-buttons.md](docs/form-buttons.md) for the full convention.

### API Client

`frontend-admin/src/lib/api/` and `frontend-user/src/lib/api/` — Axios instance with:
- Base URL from `NEXT_PUBLIC_API_BASE` (env)
- `withCredentials: true` (cookie-based auth)
- Interceptor: on 401 → calls logout API → redirects to `/login` (avoids infinite loop)

### Auth Flow

- Login sets httpOnly cookie via backend
- Next.js middleware checks cookie presence + JWT format before allowing protected routes
- Malformed cookies are cleared at middleware level

### UI Language

- User-facing labels follow [docs/glossary.md](docs/glossary.md) (column "Dipakai di UI") — default to Indonesian business terms
- Variable / function / file names stay in English

---

## Data Contract Schema — Compact Reference

Canonical: [data-contract/examples/full.yaml](data-contract/examples/full.yaml). All Pydantic models in `repository/app/model/` must match it.

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
    quality:              # column-level quality rules — same structure as dataset quality
      - code: QR002
        dimension: validity
```

**Quality dimensions** (closed enum): `completeness`, `validity`, `accuracy`

**Stakeholder roles** (closed enum): `owner`, `consumer`, `steward`, `producer`, `engineer`, `analyst`, `architect`

### Schema Versioning

`standard_version` tracks the upstream ODCS spec — **do not bump** without reading the upstream changelog.

For `metadata.version` (the contract's own version):
- **Patch** (`1.0.0 → 1.0.1`): correction to existing field description or constraint
- **Minor** (`1.0.0 → 1.1.0`): new optional fields added, backward-compatible
- **Major** (`1.0.0 → 2.0.0`): breaking change — field renamed, required field added, type changed

If a Pydantic model change would break existing saved contracts (stored as MongoDB documents), it is a **major** change and requires a migration script.

---

## Making Changes — Quick Checklist

| Change type | Touch these files |
|---|---|
| Backend model change | `repository/app/model/` + `frontend-admin/src/types/` + `frontend-user/src/types/` + verify against `data-contract/examples/full.yaml` |
| New frontend page | `src/app/(protected)/` for auth-gated, `src/app/(public)/` for open |
| nginx routing | `nginx/templates/default.conf.template` (uses envsubst — `${VAR}` syntax, not `$var`) |
| Rebuild after backend/frontend change | `docker compose build <service> && docker compose up -d <service>` |
| New endpoint | `main.py` + corresponding test in `repository/tests/` |

## Testing

```bash
make test           # all tests
make test-backend   # pytest (repository/tests/)
make test-fe-admin  # tsc --noEmit
make test-fe-user   # tsc --noEmit
```

Tests use `httpx.AsyncClient` + `unittest.mock` — no real MongoDB needed. All new routes should have a corresponding test in `repository/tests/`.

---

## Common Troubleshooting

### MongoDB won't start (WiredTiger crash)

**Symptom**: container exits immediately, logs say `No space left on device` or `WiredTiger dirty`.

**Cause**: Docker Desktop VM disk is full (not Mac host disk).

```bash
docker system prune -f && docker builder prune -f
docker compose run --rm --entrypoint "mongod --repair --dbpath /data/db" db
docker compose up -d db
```

Run `docker system prune -f` periodically on active projects.

### Frontend build fails (TypeScript)

- Variable declaration order matters: destructure `watch`/`setValue` from `form` **before** any call sites (including before `useFieldArray` hooks if `watch` is used in initializers)
- Run `docker compose build frontend-admin` to validate — TypeScript errors appear in build output

### Dev mode hot reload not working

Dev mode (`make dev`) mounts source directories as volumes and runs `next dev`. The `NEXT_PUBLIC_API_BASE` in dev overlay points to `http://localhost:8888` directly. Ensure the backend port is exposed (`docker-compose.dev.yml`).

### Backend code change not taking effect

Production mode runs from a built image — `docker compose restart backend` will **not** pick up code changes. Run:

```bash
docker compose build backend && docker compose up -d backend
```

For hot reload, use `make dev` instead.

### Backend crash-loops on startup with `DuplicateKeyError` (unique index build)

**Symptom**: `Application startup failed. Exiting.` with `E11000 duplicate key error … contract_number_1`.

**Cause**: `ensure_indexes()` tries to build a unique index on a collection that already contains duplicates (e.g., from before the index was introduced).

**Fix**: run the dedup helper, then restart the backend.

```bash
# Inspect duplicates first (replace password from .env)
docker exec beescout-db-1 mongosh \
  "mongodb://$MONGODB_USER:$MONGODB_PASS@localhost:27017/$MONGODB_DB?authSource=admin" \
  --eval 'db.dgr.aggregate([{$group:{_id:"$contract_number",c:{$sum:1}}},{$match:{c:{$gt:1}}}]).toArray()'

# Then run the dedup script (keeps oldest doc per contract_number, deletes the rest)
docker compose run --rm backend python -m scripts.dedupe_contracts --apply
docker compose restart backend
```

Script source: [repository/scripts/dedupe_contracts.py](repository/scripts/dedupe_contracts.py).

### `mongosh` says "Command requires authentication"

MongoDB root credentials live on the `admin` database, not on the app DB. Always pass `?authSource=admin`:

```bash
docker exec beescout-db-1 mongosh \
  "mongodb://admin:<password>@localhost:27017/dgrdb?authSource=admin" \
  --eval 'db.dgr.getIndexes()'
```

Password is whatever you set in `.env` as `MONGODB_PASS`.

---

## When in doubt

- **Match existing patterns** — find a similar route/component and mirror its style before inventing new abstractions
- **Don't restructure files for "cleanliness"** unless requested — single-file `main.py` is intentional
- **Ask before adding dependencies** — open a [Tech Proposal](.github/ISSUE_TEMPLATE/tech-proposal.yml) issue first
- **Verify schema changes against** `data-contract/examples/full.yaml` — that's canonical
- **Re-read this file before non-trivial work** — gotchas above are from real bugs that bit us
