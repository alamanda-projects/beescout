# Tata Kelola Proyek (Governance)

Dokumen ini menjelaskan **siapa membuat keputusan apa** di BeeScout, **bagaimana keputusan itu dibuat**, dan **bagaimana seseorang naik tier** untuk mendapat tanggung jawab lebih besar.

> **Filosofi**: BeeScout adalah proyek **AI-Native OSS**. Kontribusi non-teknis (PM, business owner, analis) sama berharganya dengan kontribusi kode. Governance ini dirancang agar keduanya punya jalur yang jelas.

---

## Tiga Tier Kontributor

### 1. Contributor

**Siapa**: Siapa saja yang membuka issue, comment, ikut diskusi, atau mengirim PR — tech maupun non-tech.

**Hak**:
- Membuka issue lewat template apapun ([Business Idea](.github/ISSUE_TEMPLATE/business-idea.yml), [Bug](.github/ISSUE_TEMPLATE/bug-report.yml), [Tech Proposal](.github/ISSUE_TEMPLATE/tech-proposal.yml))
- Mengirim Pull Request dari fork
- Berdiskusi di Issues / Discussions
- Mendapat review yang konstruktif dan tepat waktu

**Tanggung jawab**:
- Mematuhi [Kode Etik](CODE_OF_CONDUCT.md)
- Mengisi PR template lengkap, termasuk **AI Usage Disclosure** jika menggunakan AI
- Bersedia merevisi PR berdasarkan feedback reviewer

### 2. Trusted Contributor

**Siapa**: Contributor yang sudah konsisten memberikan kontribusi berkualitas. Bisa technical (PR berkualitas) atau domain-expertise (issue & desain UX yang membantu).

**Hak tambahan**:
- Triage label dan menutup issue duplikat
- Approve PR di area keahliannya (tetapi belum bisa merge sendiri)
- Disebut di [CONTRIBUTING.md](CONTRIBUTING.md) sebagai daftar kontributor aktif

**Tanggung jawab tambahan**:
- Menjaga kualitas review
- Membantu onboard kontributor baru di area yang dia kuasai
- Konsisten hadir (tidak harus full-time, tapi responsif dalam beberapa hari)

### 3. Maintainer

**Siapa**: Saat ini hanya **[@haninp](https://github.com/haninp)**. Akan berkembang ke 2–3 orang sesuai kebutuhan.

**Hak tambahan**:
- Merge PR ke `main`
- Mengubah branch protection, CODEOWNERS, dan kebijakan repo
- Membuat keputusan akhir saat ada perbedaan pendapat
- Mempromosikan Trusted Contributor menjadi Maintainer

**Tanggung jawab tambahan**:
- Menentukan arah teknis & produk (lihat [ROADMAP.md](ROADMAP.md) saat dibuat)
- Memastikan rilis tetap stabil dan aman
- Menjaga tone komunitas yang sehat

---

## Cara Naik Tier

| Dari → Ke | Kriteria | Cara |
|---|---|---|
| Contributor → Trusted | 3+ kontribusi yang ditinjau positif (PR, issue berkualitas, atau review) dalam ~3 bulan | Maintainer mengundang via issue privat. Tidak ada lamaran formal. |
| Trusted → Maintainer | 6+ bulan sebagai Trusted, kemampuan review konsisten, paham filosofi proyek | Konsensus dari maintainer yang ada. Diumumkan di Discussions. |

Tidak ada birokrasi. Kalau Anda sering muncul dan kontribusinya solid, Anda akan diundang.

---

## Kebijakan Pengambilan Keputusan

### Untuk perubahan kecil (bug fix, dokumentasi, fitur kecil)

- Cukup **1 maintainer approve** untuk merge
- Owner area (lihat [CODEOWNERS](CODEOWNERS)) di-request otomatis

### Untuk perubahan besar (breaking change, arsitektur, dependensi mayor)

- **Wajib lewat issue terlebih dahulu** — gunakan [Tech Proposal](.github/ISSUE_TEMPLATE/tech-proposal.yml)
- Diskusi terbuka selama minimal **3 hari** sebelum implementasi
- Butuh **2 maintainer approve** untuk merge (atau 1 jika hanya ada 1 maintainer)

### Untuk perubahan yang menyentuh persona / UX

- Wajib menyertakan persona terdampak di PR description
- Idealnya divalidasi oleh kontributor yang menguasai persona terkait

### Saat Ada Perbedaan Pendapat

1. Diskusi terbuka di issue/PR — fokus ke argumen, bukan orang
2. Bila buntu: Maintainer mengambil keputusan akhir, dengan alasan yang ditulis di issue
3. Keputusan Maintainer bisa di-override oleh konsensus Maintainer lain — bukan voting populer

---

## AI dalam Governance

BeeScout adalah AI-Native, jadi:

- **AI boleh membantu apa saja** — review, draft, refactor, bahkan implementasi penuh
- **Manusia tetap pemegang akun** — yang menekan tombol "merge" tetap maintainer manusia
- **AI tidak punya tier** — outputnya dinilai oleh tier kontributor manusia yang menjalankannya
- **Disclosure wajib** — lihat section "AI Usage Disclosure" di [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Branch Protection (saat di-enable di GitHub)

Setting yang akan diberlakukan untuk `main`:

- ✅ Require pull request before merging
- ✅ Require review from Code Owners
- ✅ Require status checks to pass (CI lulus)
- ✅ Dismiss stale reviews when new commits are pushed
- ❌ Allow force pushes — disabled
- ❌ Allow deletions — disabled

---

## Perubahan Governance

Governance ini bukan undang-undang. Bila proyek bertumbuh dan butuh struktur lebih, GOVERNANCE.md akan diupdate via PR biasa, dengan diskusi terbuka minimal 7 hari.

---

## English Summary

BeeScout has three contributor tiers: **Contributor** (anyone), **Trusted Contributor** (consistent quality, can triage and approve), **Maintainer** (can merge, sets direction). Promotion is invitation-based, no formal application. Currently solo-maintainer ([@haninp](https://github.com/haninp)), expanding to 2–3 trusted contributors. Major changes require a Tech Proposal issue and 3-day discussion period. AI usage is welcome with mandatory disclosure.
