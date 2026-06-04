---
name: resolve-issue
description: End-to-end workflow untuk menyelesaikan satu GitHub issue BeeScout — dari baca issue, investigasi, putuskan scope/slice, implementasi berlapis, QA, sampai buka PR. Pakai saat user minta "kerjakan #N", "lanjut ke #N", atau "selesaikan issue ini". Orkestrator yang memanggil triage-issues / prepare-pr / cleanup-branches bila perlu.
---

# Resolve a BeeScout issue (end-to-end)

Cara tim ini menyelesaikan issue. Patuhi CLAUDE.md (guardrail) — skill ini adalah operasionalisasinya. Bahasa balasan ke maintainer = Indonesia; identifier/commit/PR title = English.

## 0. Jangan langsung ngoding

PR adalah unit pengiriman. Investigasi dulu, putuskan scope, baru implementasi. Untuk task non-trivial, sampaikan rencana ringkas sebelum menulis kode.

## 1. Baca konteks (issue = sumber kebenaran, bukan chat)

```bash
gh issue view <N> --json title,body,labels,comments --jq '.title, .body'
```

Lalu cek artefak terkait sebelum mengasumsikan apa pun:
- **ADR**: `docs/adr/` — keputusan arsitektur sering sudah final (mis. ADR-0007). Issue "tech-proposal" biasanya sudah diputuskan via ADR.
- **Audit doc**: `docs/*-audit.md` (mis. `pydantic-spec-audit.md`, `form-validation-audit.md`) — peta phasing & decision sheet.
- **Riwayat**: `git log --oneline -- <file>` + `gh pr list --state merged --search "#N"` — fase mana yang **sudah** selesai. Sering kali Phase 1/2 sudah merged dan yang tersisa hanya Phase 3.
- **Spec**: `data-contract/docs/README.md` + `data-contract/examples/full.yaml` = otoritatif untuk field kontrak.

Verifikasi klaim issue terhadap kode nyata — issue/memori bisa basi.

## 2. Putuskan scope & pecah jadi slice

Issue besar (cross-cutting / "Phase 1/2/3") → **jangan satu PR raksasa**. Pecah jadi slice kecil yang:
- berdiri sendiri & bisa di-review dari mobile,
- low-risk dulu (quick win) sebelum yang butuh koordinasi/migration,
- tidak melanggar dependency (cek "blocked by", "nunggu #X").

Kalau pilihan scope benar-benar milik maintainer (mis. urutan slice, override-relax field), tanya via AskUserQuestion dengan opsi konkret. Selebihnya: ambil default paling aman dan sebutkan.

## 3. Ikuti pola yang sudah ada (jangan bikin baru)

- **strict-write / lenient-read** (#103, #114-T1.3, #102 PR-B): Pydantic tetap `Optional` (read path lenient untuk kontrak legacy, tanpa migration), enforcement required di **write-path** (`/datacontract/add` & `/update`, 422) + **FE zod** + **YAML validator** (kadang fase terpisah). Lihat docstring `Metadata` di `repository/app/model/metadata.py`.
- **3 layer berubah bareng**: backend model ↔ `frontend-admin/src/types/` ↔ `frontend-user/src/types/`. Verifikasi vs `data-contract/examples/full.yaml`.
- **Helper FE bersama**: `frontend-{admin,user}/src/lib/zod-helpers.ts` (requiredString/emailField/usernameField/strongPassword/...). Tambah ke situ, jangan duplikasi rule.
- **Migration** (kalau perlu backfill): mirror `repository/scripts/migrate_*.py` — dry-run default + `--apply`, idempoten.
- Cari route/komponen serupa dan tiru gayanya. `main.py` single-file by design — jangan split tanpa tech-proposal.

## 4. Implementasi

Sentuh file sesuai matriks "Making Changes" di CLAUDE.md. Pertahankan kepadatan komentar & idiom sekitarnya. Sertakan referensi issue di komentar kode untuk keputusan non-obvious (mis. `# #102 PR-B: ...`).

## 5. QA + buka PR

Jalankan **prepare-pr** (Definition of Done): tests + tsc + qa scripts + branch + commit + PR. Lihat skill `prepare-pr`.

## 6. Setelah merge

Tinggalkan jejak keputusan di issue/PR bila ada yang non-trivial (agent berikutnya baca issue, bukan transkrip). Update audit/ADR doc bila skill/keputusan baru muncul. Bersihkan branch (skill `cleanup-branches`).

## Anti-pattern (dari pengalaman)

- Jangan flip Pydantic ke required + migration kalau pola repo = strict-write/lenient-read → bisa breaking read legacy.
- Jangan `z.enum` untuk field yang bisa punya nilai legacy di luar enum (mis. `stakeholders.role`) tanpa cek data dulu → memblok edit kontrak lama.
- Jangan `Closes #N` kalau issue masih punya fase tersisa → pakai `Refs #N`.
- Jangan regen Postman kalau signature/path/model endpoint tidak berubah.
