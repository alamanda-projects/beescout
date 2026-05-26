# Architecture Decision Records (ADR)

> Catatan keputusan-keputusan signifikan yang membentuk BeeScout.
> Format dan proses dijelaskan di [ADR-0001](0001-record-architecture-decisions.md).

## Daftar ADR

| # | Judul | Status | Tanggal |
|---|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Mencatat Keputusan Arsitektur | Diterima | 2026-05-10 |
| [0002](0002-agpl-3-license.md) | Memilih AGPL-3.0 sebagai Lisensi | Diterima | 2026-05-10 |
| [0003](0003-impact-severity-split.md) | Pisah Impact & Severity di Quality Rule | Diterima | 2026-05-22 |
| [0004](0004-approval-workflow-multi-role.md) | Approval Workflow Multi-Peran | Superseded by ADR-0005 | 2026-05-24 |
| [0005](0005-approval-owner-replaces-steward.md) | Approver = Owner + Producer + Consumer | Diterima | 2026-05-24 |
| [0007](0007-consumer-producer-representation.md) | Konsolidasi Representasi Konsumen/Produser | Proposed | 2026-05-26 |

## Status — Legenda

- **Proposed**: Sedang didiskusikan; belum berlaku
- **Diterima**: Berlaku — kontributor dan AI harus mengikutinya
- **Ditolak**: Tidak diberlakukan, didokumentasikan agar tidak diusulkan ulang
- **Deprecated**: Tidak lagi berlaku, tidak ada penggantinya yang formal
- **Superseded by ADR-XXXX**: Digantikan oleh ADR baru

## Cara Mengusulkan ADR Baru

Lihat [ADR-0001](0001-record-architecture-decisions.md) — ringkasan:

1. Buka [🏗️ Tech Proposal](../../.github/ISSUE_TEMPLATE/tech-proposal.yml) untuk diskusi
2. Setelah konsensus, buka PR: tambah file `NNNN-judul-singkat.md` di folder ini
3. Update tabel daftar ADR di file ini
4. Status awal `Proposed`, berubah jadi `Diterima` saat PR di-merge

## Mengapa ADR Penting di Proyek AI-Native?

AI tidak punya memori antar sesi. Tanpa ADR yang jelas:

- AI di sesi berikutnya bisa mengusulkan ulang opsi yang sudah ditolak
- Kontributor manusia baru harus rewind seluruh diskusi historical
- Diskusi di issue/PR mudah hilang dalam volume

ADR adalah cara membuat keputusan **terbaca dan tahan waktu** — manusia maupun AI bisa mengakses konteks lengkap dari satu file.
