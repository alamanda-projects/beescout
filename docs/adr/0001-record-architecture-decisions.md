# ADR-0001: Mencatat Keputusan Arsitektur

- **Status**: Diterima
- **Tanggal**: 2026-05-10
- **Pengusul**: [@haninp](https://github.com/haninp)

## Konteks

BeeScout berkembang dengan kontribusi dari pelbagai sumber: maintainer, kontributor manusia, dan AI agent (Claude Code). Tanpa jejak yang jelas, "mengapa kita memutuskan X" mudah hilang seiring rotasi kontributor — dan pertanyaan yang sama akan muncul berulang.

Tantangan spesifik untuk proyek **AI-Native**:

- AI tidak punya memori antar sesi. Kalau alasan keputusan tidak ditulis, AI di sesi berikutnya akan mengusulkan ulang opsi yang sudah ditolak.
- Kontributor non-tech masuk dan keluar — mereka butuh konteks "kenapa begini, bukan begitu" tanpa harus baca seluruh git history.
- Diskusi di GitHub Issues bisa hilang dalam volume — yang permanen adalah file di repo.

## Keputusan

Setiap keputusan arsitektur signifikan akan dicatat sebagai **Architecture Decision Record (ADR)** di `docs/adr/`.

### Yang dianggap "signifikan"

ADR diperlukan saat keputusan:

- Mengubah filosofi proyek (mis. cara kontribusi, lisensi, governance)
- Memilih satu teknologi/pendekatan dari beberapa yang masuk akal
- Mengunci sebuah trade-off jangka panjang (mis. single-file `main.py`, MongoDB vs RDBMS)
- Menolak ide yang bagus tapi tidak cocok dengan arah proyek (lihat "Not Planned" di [ROADMAP.md](../../ROADMAP.md))

ADR **tidak** diperlukan untuk:

- Bug fix
- Refactor lokal yang tidak mengubah perilaku
- Penambahan fitur kecil yang konsisten dengan pola yang ada

### Format

Satu file Markdown per ADR. Penomoran berurutan, padding 4 digit (`0001`, `0002`, ...). Nama file: kebab-case singkat dari judul.

Setiap ADR berisi:

```markdown
# ADR-NNNN: Judul Singkat

- **Status**: Proposed | Diterima | Ditolak | Deprecated | Superseded by ADR-XXXX
- **Tanggal**: YYYY-MM-DD
- **Pengusul**: @username

## Konteks
[Apa kondisi/masalah yang membuat keputusan ini perlu? Apa yang sebelumnya tidak jelas?]

## Keputusan
[Apa yang diputuskan? Tulis dalam present tense. Sespesifik mungkin.]

## Alternatif yang Dipertimbangkan
[Pilihan lain dan alasan tidak dipilih.]

## Konsekuensi
[Apa yang terjadi setelah keputusan ini? Positif, negatif, dan netral.]

## Referensi
[Link ke issue, PR, diskusi, atau dokumen eksternal yang relevan.]
```

### Status — Siklus Hidup

| Status | Arti |
|---|---|
| **Proposed** | Sedang didiskusikan; belum berlaku |
| **Diterima** | Berlaku — kontributor dan AI harus mengikutinya |
| **Ditolak** | Tidak diberlakukan, didokumentasikan agar tidak diusulkan ulang |
| **Deprecated** | Tidak lagi berlaku, tapi tidak ada penggantinya yang formal |
| **Superseded by ADR-XXXX** | Digantikan oleh ADR baru — link ke ADR pengganti |

ADR yang sudah Diterima **tidak diedit isinya** — yang berubah hanya status. Bila keputusan perlu direvisi, buat ADR baru yang men-supersede.

### Proses Pengajuan

1. Buat issue [🏗️ Tech Proposal](../../.github/ISSUE_TEMPLATE/tech-proposal.yml) untuk diskusi
2. Setelah ada konsensus, buka PR yang menambah file ADR baru di `docs/adr/`
3. Status awal: `Proposed`
4. Setelah PR di-merge oleh maintainer dengan status `Diterima` — ADR berlaku
5. Update [`docs/adr/README.md`](README.md) (index) saat menambah ADR baru

## Alternatif yang Dipertimbangkan

### a. Hanya pakai GitHub Issues / Discussions

Kelebihan: tidak ada tooling baru.
Kekurangan: tidak ter-version dengan kode, sulit ditemukan kembali, mudah hilang dalam volume issue.

### b. Wiki GitHub

Kelebihan: lebih leluasa.
Kekurangan: terpisah dari kode, tidak melalui review PR, tidak bisa di-link dari source code dengan permalink yang stabil.

### c. RFC formal (ala Rust / Python PEP)

Kelebihan: sangat rigorous.
Kekurangan: overkill untuk fase awal proyek. ADR lebih ringan dan bisa di-upgrade ke RFC nanti bila perlu.

## Konsekuensi

**Positif**:
- Kontributor baru (manusia atau AI) bisa cepat paham "kenapa begini" dengan baca `docs/adr/`
- Diskusi keputusan ter-link langsung dengan kode (via PR)
- Mengurangi pengulangan diskusi keputusan yang sudah pernah selesai

**Negatif**:
- Tambah satu langkah saat membuat keputusan signifikan
- Risiko ADR tidak ditulis untuk keputusan yang seharusnya didokumentasikan — perlu disiplin reviewer

**Netral**:
- ADR adalah dokumen Indonesia (selaras dengan dokumen utama lain). Header field (`Status`, `Tanggal`) tetap pakai istilah baku.

## Referensi

- Michael Nygard, [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — ide asli ADR
- [adr.github.io](https://adr.github.io/) — pranala kumpulan template & tooling
