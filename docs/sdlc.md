# SDLC Standar — BeeScout

> Software Development Life Cycle yang berlaku di BeeScout. Dokumen ini menjelaskan **bagaimana sebuah ide bergerak dari issue → release** dan **gate apa yang harus dilewati di tiap tahap**.
>
> Filosofi: **trunk-based development**, **AI-native collaboration**, **persona-driven verification**, **branch-protected main**.

## Mengapa kita butuh ini

Tanpa standar yang ditulis:
- Kontributor baru (manusia atau AI) tidak tahu kapan harus tes, kapan boleh push, kapan butuh ADR
- Review menjadi inkonsisten — beberapa PR di-review ketat, sebagian lewat
- "Done" punya arti berbeda di setiap orang
- Saat AI mengeksekusi via Claude Code, AI butuh checklist yang jelas agar hasilnya konsisten

SDLC ini menyatukan semua dokumen workflow yang sudah ada ([CONTRIBUTING.md](../CONTRIBUTING.md), [GOVERNANCE.md](../GOVERNANCE.md), [CLAUDE.md](../CLAUDE.md), [ci_cd.md](ci_cd.md), template issue/PR) ke dalam satu **alur 7 tahap** yang bisa diikuti tanpa lompat-lompat.

---

## Alur 7 Tahap

```
┌────────┐   ┌────────┐   ┌─────────┐   ┌──────┐   ┌────────┐   ┌───────┐   ┌─────────┐
│ 1 PLAN │ → │2 DESIGN│ → │3 DEVELOP│ → │4 TEST│ → │5 REVIEW│ → │6 MERGE│ → │7 RELEASE│
└────────┘   └────────┘   └─────────┘   └──────┘   └────────┘   └───────┘   └─────────┘
   issue        ADR         feature        CI           PR        main       changelog
                          branch                       gate                   tag (opt)
```

Setiap tahap punya **input → aktivitas → output** yang eksplisit.

### Tahap 1 — PLAN (Perencanaan)

**Input**: Friction / ide / bug yang dirasakan.

**Aktivitas**:
- Cek issue serupa di GitHub Issues (hindari duplikat)
- Buka [issue baru](https://github.com/alamanda-projects/beescout/issues/new/choose) dengan template yang tepat:
  - [💡 Business Idea](../.github/ISSUE_TEMPLATE/business-idea.yml) — non-tech, bahasa natural
  - [🐛 Bug Report](../.github/ISSUE_TEMPLATE/bug-report.yml) — reproduce + expected
  - [🏗️ Tech Proposal](../.github/ISSUE_TEMPLATE/tech-proposal.yml) — implementation plan
- Diskusi terbuka di issue: persona terdampak, scope, success criteria

**Output**: Issue dengan label `needs-triage`.

**Definition of Ready** (sebelum naik ke tahap 2):

- [ ] Persona terdampak teridentifikasi (lihat [docs/personas.md](personas.md))
- [ ] Problem statement jelas, bukan solusi
- [ ] Success criteria spesifik dan terukur dari sudut user
- [ ] Maintainer sudah triage label (mis. `enhancement`, `ux`, `bug`)
- [ ] Scope disepakati — apakah 1 PR atau split jadi beberapa
- [ ] Untuk perubahan besar: butuh ADR? lihat [ADR-0001](adr/0001-record-architecture-decisions.md)

### Tahap 2 — DESIGN (Perancangan)

**Input**: Issue yang sudah memenuhi Definition of Ready.

**Aktivitas**:
- **Untuk perubahan kecil**: skip ke Tahap 3
- **Untuk perubahan besar/breaking**: tulis [ADR](adr/) baru
  - Format: `docs/adr/NNNN-judul-singkat.md`
  - Status awal: `Proposed`
  - Update index di [docs/adr/README.md](adr/README.md)
- Diskusi minimal **3 hari** terbuka di issue (lihat [GOVERNANCE.md](../GOVERNANCE.md) — kebijakan keputusan)
- Untuk perubahan UX yang menyentuh persona: tambah mockup ASCII / Figma / screenshot di issue

**Output**: ADR di status `Proposed` (kalau berlaku) + konsensus di issue.

**Definition of Ready** (sebelum naik ke tahap 3):

- [ ] Desain teknis sudah tertulis (di issue atau ADR)
- [ ] Tidak ada blocker / pertanyaan terbuka yang belum dijawab
- [ ] File yang akan disentuh sudah teridentifikasi
- [ ] Strategi pengujian terdefinisi (mau test apa, gimana cara)

### Tahap 3 — DEVELOP (Implementasi)

**Input**: Issue + desain yang sudah disepakati.

**Aktivitas**:
- Fork repo (atau buat branch langsung kalau Trusted Contributor+)
- Naming branch: `<type>/<issue-number>-<kata-kunci>`
  - Contoh: `feat/1-tooltip-bilingual`, `fix/12-login-timeout`, `docs/adr-0003-impact`
  - Types: `feat | fix | docs | refactor | test | chore`
- Implementasi mengikuti konvensi di [CLAUDE.md](../CLAUDE.md)
- Commit kecil dan sering, pesan jelas

**AI Usage**: penuh disambut. Lihat [CONTRIBUTING.md — Cara Berkolaborasi dengan AI](../CONTRIBUTING.md#cara-berkolaborasi-dengan-ai).

**Output**: Branch dengan commit yang siap di-push.

**Definition of Ready** (sebelum naik ke tahap 4):

- [ ] Kode kompilasi & jalan lokal (`make dev`)
- [ ] Konvensi kode di [CLAUDE.md](../CLAUDE.md) diikuti
- [ ] Tidak ada secret, token, atau kredensial yang di-commit
- [ ] Glossary/dokumentasi terupdate kalau ada istilah/perilaku baru

### Tahap 4 — TEST (Pengujian)

**Input**: Implementasi lokal.

Strategi pengujian berlapis (test pyramid):

| Layer | Cakupan | Alat | Wajib kapan |
|---|---|---|---|
| **Unit / Pydantic** | Validasi model, util function | `pytest` | Setiap PR backend |
| **Type check** | TypeScript types | `tsc --noEmit` | Setiap PR frontend |
| **Integration** | API endpoint + mocked Mongo | `httpx.AsyncClient` | PR yang menyentuh endpoint baru |
| **Build verification** | Docker image bisa di-build | `docker compose build` | PR yang ubah Dockerfile/deps |
| **Manual UI** | Browser flow sesuai persona | Manual + screenshot | PR yang ubah UI |
| **Persona-based smoke test** | Skenario user end-to-end | Manual oleh reviewer | Sebelum merge ke main |

**Persona-based smoke test** — kunci QA BeeScout. Lihat section "QA Process" di bawah.

Lihat detail tooling di [docs/ci_cd.md](ci_cd.md).

**Output**: Bukti pengujian (screenshot, output terminal, log).

**Definition of Ready** (sebelum naik ke tahap 5):

- [ ] `make test` lulus lokal
- [ ] Bukti manual test tersimpan (screenshot/video/output)
- [ ] Edge case sudah dicek (input kosong, panjang ekstrem, network error)
- [ ] Tidak ada console error / warning baru di browser dev tools

### Tahap 5 — REVIEW (Tinjauan)

**Input**: Branch di-push, PR dibuka.

**Aktivitas**:
- PR template otomatis muncul — isi lengkap, terutama **AI Usage Disclosure**
- [CODEOWNERS](../CODEOWNERS) otomatis di-request review (saat ini: @haninp)
- CI berjalan otomatis (3 status check wajib hijau)
- Reviewer membaca diff, tanya klarifikasi via "Review comments"
- Author balas comment, push perbaikan (review otomatis di-dismiss karena stale)
- Loop sampai approved

**Output**: PR dengan status approved + CI hijau.

**Definition of Ready** (sebelum naik ke tahap 6):

- [ ] PR template terisi semua field
- [ ] AI Usage Disclosure dicentang dengan jujur
- [ ] Persona terdampak disebut + link issue
- [ ] CI 3 check hijau
- [ ] Approved CODEOWNERS (saat ini @haninp)
- [ ] Conversation threads resolved
- [ ] Branch up-to-date dengan main (`git fetch origin && git rebase origin/main`)

### Tahap 6 — MERGE (Penggabungan)

**Input**: PR yang lulus tahap 5.

**Aktivitas**:
- Maintainer (@haninp) klik **Squash and merge** di GitHub
- Squash message default = PR title
- Branch fork otomatis dihapus
- Issue auto-close kalau pakai `Closes #N` di PR description

**Output**: Commit baru di `main` + branch source terhapus.

> **Aturan**: tidak ada `git push` langsung ke `main`. Branch protection mencegah ini. Lihat [GOVERNANCE.md — Branch Protection](../GOVERNANCE.md#branch-protection--aktif-di-main).

### Tahap 7 — RELEASE (Rilis)

BeeScout pre-1.0 — belum ada cadence rilis ketat. Aktivitas yang **tetap dilakukan** setiap merge ke main:

**Aktivitas**:
- Update [CHANGELOG.md](../CHANGELOG.md) — bagian "Unreleased"
- Bila perubahan signifikan: catat di "Now" → "Done" di [ROADMAP.md](../ROADMAP.md)
- Untuk milestone (0.1, 0.2, dst): buat git tag + GitHub Release dengan release notes dari CHANGELOG

**Output**: Repo state yang siap dipakai komunitas.

---

## Definition of Done — Ringkasan

Sebuah perubahan dianggap **DONE** bila:

| Kategori | Kriteria |
|---|---|
| **Fungsional** | Fitur bekerja sesuai success criteria di issue. Verified via manual + automated test. |
| **Konvensi** | Kode mengikuti [CLAUDE.md](../CLAUDE.md). UI mengikuti [docs/glossary.md](glossary.md). |
| **Dokumentasi** | CHANGELOG diupdate. Glossary diupdate kalau ada istilah baru. ADR kalau ada decision arsitektur. |
| **Persona** | Validated dari sudut pandang persona terdampak (lihat QA Process). |
| **Otomasi** | CI hijau. PR template terisi. AI Usage Disclosed. |
| **Governance** | Approval CODEOWNERS. Conversation resolved. Squash-merged. |

---

## QA Process — Persona-Based Smoke Test

Ini diferensiator BeeScout dari proyek OSS biasa. Sebelum merge, reviewer **memerankan persona terdampak** dan menjalankan skenario use case nyata.

### Cara

1. Cek out branch PR: `gh pr checkout <PR-number>`
2. `make dev` — jalankan lokal
3. Login sebagai akun yang mensimulasikan persona:
   - Pak Bambang → akun `root`
   - Bu Retno → akun `admin`
   - Mas Dimas → akun `developer`
   - Mbak Indah → akun `user`
4. Jalankan skenario dari sudut pandang persona itu
5. Catat friction baru — bila ada, comment di PR sebelum approve

### Template skenario per persona

Setiap PR yang mengubah UI harus punya skenario eksplisit di description. Format minimum:

```markdown
## Persona Smoke Test

**Skenario: Bu Retno menulis aturan kualitas untuk kolom 'email'**

1. Login sebagai admin (Bu Retno)
2. Buka /contracts/new → Step 3 (Struktur Data)
3. Tambah kolom: name=email, type=string
4. Tambah aturan kualitas: dimension=validity
5. Pilih severity & impact
6. Lanjut ke Step 4, simpan

**Expected**: Bu Retno paham field yang harus diisi tanpa googling istilah.
**Friction yang perlu dicari**: ada field yang dia ragu? istilah yang bingung? tombol yang nggak intuitif?
```

---

## Cadence & Iterasi

BeeScout **tidak pakai sprint formal**. Lebih cocok:

- **Continuous flow** — issue diambil saat kontributor punya kapasitas
- **ROADMAP horizons** sebagai north star: lihat ["Now / Next / Later"](../ROADMAP.md)
- **Review SLA**: maintainer akan respon PR/issue dalam **7 hari kerja** (lebih cepat saat aktif)
- **Stale PR**: PR tanpa update >30 hari akan dimark `stale`, ditutup setelah +14 hari tanpa respons

---

## Contoh Konkret: Eksekusi Track UX (Issue #1-4)

Sebagai contoh penerapan SDLC ini, lihat 4 Tech Proposal yang baru dibuka:

| Issue | Tahap saat ini | Catatan |
|---|---|---|
| [#1 Tooltip bilingual](https://github.com/alamanda-projects/beescout/issues/1) | Tahap 1 (Plan) → 2 (Design) | Sudah ada desain di issue, tidak butuh ADR karena non-breaking |
| [#2 Group stakeholder](https://github.com/alamanda-projects/beescout/issues/2) | Tahap 1 → 2 | Non-breaking, langsung lanjut Tahap 3 saat ada eksekutor |
| [#3 Helper text tipe data](https://github.com/alamanda-projects/beescout/issues/3) | Tahap 1 → 2 | Sekalian update glossary |
| [#4 Pisah impact + severity](https://github.com/alamanda-projects/beescout/issues/4) | Tahap 1, butuh ADR-0003 sebelum Tahap 3 | Breaking change — wajib lewat Tahap 2 (Design) penuh |

Issue #1 dipilih sebagai **first PR** untuk uji jalannya SDLC ini end-to-end.

---

## Saat Standar Ini Berubah

SDLC bukan undang-undang. Bila ada kebutuhan baru (mis. proyek tumbuh, butuh sprint, perlu release otomatis), update via PR ke dokumen ini — sama seperti dokumen lain. ADR baru bisa men-supersede aturan tertentu kalau ada perubahan besar.

---

## English Summary

BeeScout follows a 7-stage SDLC: **Plan → Design → Develop → Test → Review → Merge → Release**. Each stage has explicit input, activities, output, and a "Definition of Ready" gate. Key differentiator: **persona-based smoke testing** before merge — reviewer roleplays the affected persona and reports friction. No formal sprints — continuous flow guided by [ROADMAP](../ROADMAP.md) horizons. All merges go through PR with CODEOWNERS approval and 3 CI checks (enforced via branch protection on `main`).
