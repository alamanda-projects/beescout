---
name: prepare-pr
description: Jalankan Definition of Done BeeScout lalu buka PR — tests + tsc + qa scripts + (regen postman bila perlu) + branch + commit (conventional) + PR (test plan). Pakai saat perubahan sudah siap dan user minta "buka PR", "siapkan PR", atau setelah implementasi selesai.
---

# Prepare PR (Definition of Done)

## 1. QA gauntlet — semua harus hijau dulu

**Backend tests** — `pip`/`pytest` TIDAK terinstal global di mesin ini; pakai venv repo:

```bash
cd repository && ../.venv/bin/python -m pytest tests/ -q
```

(`make test-backend` gagal karena `pip: command not found` — gunakan `.venv/bin/python -m pytest` langsung.)

**Frontend typecheck** (kalau FE berubah):

```bash
make test-fe-admin    # cd frontend-admin && npx tsc --noEmit
make test-fe-user     # cd frontend-user && npx tsc --noEmit
```

**QA scripts** (dua ini jalan di CI — harus exit 0):

```bash
bash scripts/qa-form-buttons.sh
bash scripts/qa-prod-readiness.sh
```

> `qa-prod-readiness.sh` bisa gagal di **lokal** karena `.env` dev (`COOKIE_SECURE=false`, `ALLOWED_ORIGINS http://`). Itu **pre-existing**, bukan regresi — di CI (tanpa `.env`) auto-skip. Laporkan apa adanya, jangan "perbaiki" .env.

**Postman** — regen HANYA bila endpoint berubah (path/method/request/response/description di `main.py` atau `repository/app/model/`):

```bash
make regen-postman   # butuh docker; commit docs/api/beescout.postman_collection.json bila ada diff
```

Penambahan logika internal/422 yang tidak mengubah OpenAPI → **tidak** perlu regen.

## 2. Branch

`<type>/<issue#>-<slug>`, type ∈ `fix|feat|chore|docs|refactor`. Cabang dari `main` terbaru:

```bash
git checkout main && git pull --ff-only && git checkout -b feat/<N>-<slug>
```

## 3. Commit (conventional, body Indonesia OK)

Subject English conventional-commit. Jelaskan WHY + pendekatan (mis. "strict-write/lenient-read"). Trailer:

```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

## 4. PR

```bash
git push -u origin <branch>
gh pr create --base main --title "<conventional title>" --body "<...>"
```

Body wajib memuat:
- Ringkasan + **pendekatan** (kalau menyimpang dari draft audit, jelaskan kenapa).
- **`Closes #N`** kalau issue tuntas; **`Refs #N`** kalau masih ada fase tersisa.
- Test plan checklist (hasil QA di atas, termasuk catatan qa-prod-readiness bila relevan).
- Footer: `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

## 5. Merge

Squash-merge only (default repo); branch dihapus saat merge. **Jangan merge sendiri** kecuali maintainer eksplisit minta. Bila branch protection memblok dan maintainer (admin) sudah memerintahkan merge:

```bash
gh pr merge <N> --squash --delete-branch --admin   # --admin hanya atas instruksi eksplisit; laporkan transparan
```

Setelah merge → jalankan `cleanup-branches`.
