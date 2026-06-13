# Panduan Menulis Issue BeeScout

> Brief ini melengkapi form template di [`.github/ISSUE_TEMPLATE/`](../.github/ISSUE_TEMPLATE/).
> Template `.yml` meng-encode **field wajib** (persona, area, severity); panduan ini menjelaskan
> **anatomi body** yang seharusnya dihasilkan — bagian yang bikin issue actionable.

## Prinsip dasar

- **Issue = source of truth** untuk pekerjaan pending — bukan chat, bukan memory. Agent lain
  (cloud/lokal) membaca issue, bukan transkrip. (Lihat [CLAUDE.md](../CLAUDE.md).)
- **Bahasa**: judul & istilah teknis dalam English (conventional-commit style); narasi boleh
  Bahasa Indonesia.
- **Tanggal selalu absolut** (mis. "6 Juni 2026"), bukan "kemarin".
- Tiga jalur sesuai persona penulis → tiga template. Pilih berdasarkan **siapa yang menulis &
  seberapa matang idenya**, bukan ukuran kerjaan.

## Kapan pakai yang mana

| Template | Untuk | Pemicu |
|---|---|---|
| 💡 **Ide Bisnis** | PM/Analis/Owner — tahu masalah, tak harus tahu teknis | "Susah/lambat ngapain", belum ada solusi konkret |
| 🐛 **Bug Report** | Siapa saja — ada yang rusak | Perilaku ≠ ekspektasi |
| 🏗️ **Tech Proposal** | Dev/Arsitek — sudah kepikiran implementasi | Refactor, breaking change, dependency baru, split file |

---

## 1. 💡 User Story / Ide Bisnis

Format inti = **"As a / I want / so that"** dibungkus konteks masalah.

```markdown
## Persona terdampak
Mbak Indah (User / Business Analyst)   ← pilih dari docs/personas.md

## Masalah
Kondisi sekarang & apa yang menyulitkan (bahasa natural, ada angka kalau bisa).
> Contoh: "Untuk cek kontrak lewat masa retensi, harus scroll satu-satu.
> Tidak ada filter expired."

## User story
Sebagai **Business Analyst**, saya ingin **memfilter kontrak yang expired**,
agar **bisa menindak retensi tanpa scroll manual**.

## Kriteria penerimaan (Definition of Done bisnis)
- [ ] Ada filter "Status: Expired" di daftar kontrak
- [ ] Hasil filter menampilkan tanggal expiry
- [ ] Kosong → empty state, bukan error

## Dampak kalau tidak dikerjakan / nilai
Singkat: siapa terbantu, seberapa sering.
```

**Aturan:** jangan menulis solusi teknis di sini — itu tugas triage/tech-proposal. Acceptance
criteria harus **observable** (bisa dicek tanpa lihat kode).

---

## 2. 🐛 Bug Report

Inti = **reproducibility**. Tanpa langkah reproduksi, bug tidak actionable.

```markdown
## Area
Frontend Admin / Backend / dst.

## Apa yang terjadi
Gejala singkat + (kalau ada) pesan error / screenshot.

## Apa yang diharapkan
Perilaku benar yang seharusnya.

## Langkah reproduksi
1. Login sebagai admin
2. Buka /contracts/new → isi SLA → kosongkan retention
3. Klik Simpan
→ halaman blank, tanpa toast

## Lingkungan
Branch/commit, browser, prod/dev.

## Severity (dugaan)
blocker / major / minor — boleh dikoreksi saat triage.
```

**Aturan:** "Expected vs Actual" wajib eksplisit. Kalau menyangkut keamanan → **jangan** issue
publik, lewat [SECURITY.md](../SECURITY.md).

---

## 3. 🏗️ Tech Proposal / slice kerjaan

Pola untuk issue eksekusi (mis. issue slice dari sebuah epik).

```markdown
## Konteks (WHY)
Latar belakang + link ke epik induk (mis. "Spin-off #102 PR-B slice 5").

## Scope (WHAT)
Daftar bernomor, eksplisit file yang disentuh:
1. Wizard SLA step — frontend-{admin,user}/.../page.tsx
2. Write-path backend — main.py (422 enforcement)
3. YAML validator
4. Tests

## Pendekatan / trade-off
Pola yang dipilih + alasan (mis. "strict-write/lenient-read → tidak
breaking kontrak legacy").

## Out of scope
Apa yang sengaja TIDAK dikerjakan (cegah scope creep).

## Verifikasi
Test plan: tests, tsc, qa scripts, regen postman bila perlu.

## Breaking change?
Ya/Tidak — kalau ya, butuh migration script (lihat CLAUDE.md).

Refs #<epik>   ← atau "Closes #N" kalau issue ini tuntas sendiri
```

---

## Konvensi lintas-template (selalu)

| Elemen | Aturan |
|---|---|
| **Judul** | `type(scope): ringkas` — `[Bug]`/`[Idea]`/`[Tech]` prefix dari template; conventional untuk issue eksekusi (`feat(model): ...`) |
| **Trailer** | `Closes #N` (tuntas) vs `Refs #N` (masih ada fase lain) — **pilih sadar** |
| **Epik vs slice** | Epik besar dipecah jadi slice kecil yang masing-masing 1 PR; tiap slice `Refs` epik |
| **Label** | `needs-triage` default; `enhancement`/`bug`/`tech-proposal` sesuai jenis |
| **Checklist** | Acceptance criteria & test plan selalu `- [ ]` agar bisa dicentang |
| **Link** | Tautkan file/PR/issue/persona terkait — agent berikutnya menelusuri lewat ini |

---

## Lihat juga

- [CONTRIBUTING.md](../CONTRIBUTING.md) — dua jalur kontribusi (Commander / Architect)
- [docs/personas.md](personas.md) — 4 persona untuk field "siapa terdampak"
- [docs/sdlc.md](sdlc.md) — lifecycle dari issue → PR → merge
- [docs/glossary.md](glossary.md) — istilah bisnis ↔ teknis untuk UI strings
