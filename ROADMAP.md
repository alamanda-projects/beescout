# BeeScout Roadmap

> **Filosofi**: Roadmap ini hidup. Item bergeser tier saat prioritas berubah, kontributor hadir/pergi, atau realita teknis menuntut adaptasi.
>
> **Cara baca**: tiga "horizon" — apa yang sedang dikerjakan, yang akan datang, dan yang ada di radar tapi belum dijadwalkan.

## Cara Item Masuk Roadmap

1. Issue dibuka via [💡 Ide Bisnis](.github/ISSUE_TEMPLATE/business-idea.yml) atau [🏗️ Tech Proposal](.github/ISSUE_TEMPLATE/tech-proposal.yml)
2. Maintainer triage: assign label & milestone, atau diskusi ulang ruang lingkupnya
3. Bila disetujui: masuk ke salah satu horizon di bawah, dengan link ke issue
4. Bila tidak: ditutup dengan alasan, atau dibiarkan terbuka untuk diskusi lebih lanjut

> Tidak ada deadline keras. Estimasi ditulis sebagai "horizon", bukan tanggal.

---

## 🎯 Now — Sedang Dikerjakan

> Yang sedang aktif diimplementasikan atau di-review.

### Tes UX Internal — Standar Pengelolaan Data Contract
Saat ini BeeScout sedang masuk fase **uji coba internal** untuk memvalidasi alur pengelolaan kontrak data dari sudut pandang keempat persona ([docs/personas.md](docs/personas.md)). Yang sedang divalidasi:
- Alur tambah / edit / setujui kontrak — apakah sudah cukup intuitif untuk Bu Retno?
- Bahasa istilah di UI — apakah Mbak Indah paham tanpa perlu glosarium di sebelahnya?
- Batas akses & keamanan — apakah Pak Bambang merasa kontrol cukup ketat?
- Detail teknis (physical type, schema, SA Key) — apakah cukup presisi untuk Mas Dimas?

Output fase ini: catatan UX & friction yang akan menjadi backlog perbaikan untuk milestone berikutnya.

### Merangkum Desain "Quality Rules"
Aturan kualitas data adalah komponen sentral dari Data Contract, tapi caranya ditulis & disimpan masih dalam eksplorasi:
- **Format penulisan** — bagaimana sebuah aturan dideklarasikan agar mudah dibaca steward, tapi cukup formal untuk dieksekusi engine?
- **Reusability** — kapan aturan jadi bagian dari katalog reusable, kapan inline?
- **Hubungan dengan dimensi** (`completeness`, `validity`, `accuracy`) — apakah cukup, atau perlu dimensi tambahan?
- **Eksekusi** — saat ini definisi-saja; eksekusi (mis. via Great Expectations) ada di "Later"

Output fase ini: dokumen referensi `docs/quality_rules_design.md` yang akan jadi sumber kebenaran untuk implementasi UI & validasi backend.

---

## 🚀 Next — Antrian Berikutnya

> Sudah disepakati akan dikerjakan, tinggal menunggu kapasitas. Detail desain mungkin masih perlu finalisasi.

### Stabilitas & Keamanan
- **Branch protection rule di `main`** — require review dari Code Owner, require CI lulus, no force-push. Lihat [GOVERNANCE.md](GOVERNANCE.md).
- **Audit log endpoint sensitif** — siapa membuat/menghapus user, siapa approve apa. Berguna untuk Pak Bambang.
- **Test coverage backend ≥ 60%** — saat ini sebagian endpoint baru belum punya test.

### Pengalaman Kontributor
- **Tutorial "Kontribusi pertama dalam 30 menit"** — alur konkret untuk PM/non-tech: dari fork → buka business-idea → AI menerjemahkan → PR. Akan jadi bagian dari [getting-started.md](getting-started.md).
- **Demo seed data** — script `make seed` yang isi DB dengan kontrak contoh agar kontributor baru bisa eksplor tanpa perlu buat data sendiri.

### Fitur Pengguna
- **Notifikasi approval di sidebar admin** — sudah ada badge angka pending; tambah toast saat ada approval baru di sesi yang sedang berjalan.
- **Filter & search yang lebih kuat** di Data Contract list (by tipe, owner, status approval).

---

## 🌌 Later — Ada di Radar

> Ide bagus tapi belum waktunya. Bisa naik ke "Next" saat kondisi matang (kontributor, kebutuhan dari komunitas, dll).

### Skala & Multi-tenant
- **Multi-organisasi dalam satu instance** — saat ini satu instance = satu organisasi. Bisa jadi dibutuhkan saat ada partner yang ingin pakai BeeScout untuk beberapa anak perusahaan.
- **Soft-delete untuk kontrak** — saat ini hard-delete. Untuk regulated industry mungkin perlu retain dengan tombstone.

### Integrasi
- **Webhook saat kontrak berubah** — agar pipeline downstream bisa subscribe.
- **Plugin untuk CI tools** — GitHub Actions / GitLab CI step yang validasi schema PR terhadap kontrak.
- **Sinkronisasi dengan data catalog lain** (DataHub, OpenMetadata, Atlan) — ekspor/impor metadata.

### Kualitas Data
- **Eksekusi quality rule otomatis** — saat ini katalog aturan masih definisi; eksekusi (mis. Great Expectations) belum.
- **Quality score per kontrak** — agregat hasil eksekusi rule jadi skor 0-100 yang ditampilkan ke Mbak Indah.

### Internasionalisasi
- **Bahasa Inggris penuh di UI** — untuk komunitas global. Saat ini ID-first.

---

## ❌ Not Planned

> Hal yang **tidak akan** dikerjakan, kecuali ada perubahan filosofi proyek. Dicantumkan agar kontributor tidak menghabiskan waktu mengusulkan.

- **Mengganti MongoDB ke RDBMS** — schema kontrak fleksibel, MongoDB cocok. Ganti hanya jika ada alasan operasional kuat.
- **Membuat BeeScout jadi SaaS multi-tenant cloud** — proyek ini didesain untuk self-host. SaaS adalah produk turunan, bukan core.
- **Menghapus filosofi AI-Native** — kontribusi via AI tetap di pusat proyek.

---

## Bagaimana Dengan Versi Rilis?

BeeScout saat ini di fase **pre-1.0**. Tidak ada commitment versi semantik untuk API publik sampai 1.0.

Roadmap menuju 1.0:

| Milestone | Kriteria |
|---|---|
| **0.1** *(saat ini)* | Foundation: CRUD kontrak, approval, user management, role gating — **sedang divalidasi via tes UX internal & desain quality rules** |
| **0.2** | UX standar yang lebih matang dari hasil tes internal, desain quality rules tertulis, branch protection aktif, demo seed data |
| **0.5** | Test coverage backend ≥ 60%, audit log, notifikasi real-time, filter/search lebih kuat |
| **1.0** | Stable API yang dijanjikan backward-compatible, dokumentasi lengkap, minimal 3 deployment di production |

---

## Bagaimana Cara Kontribusi ke Roadmap?

| Yang ingin Anda lakukan | Caranya |
|---|---|
| Usulkan fitur baru | Buka [💡 Ide Bisnis](.github/ISSUE_TEMPLATE/business-idea.yml) |
| Usulkan perubahan teknis besar | Buka [🏗️ Tech Proposal](.github/ISSUE_TEMPLATE/tech-proposal.yml) |
| Tantang asumsi roadmap | Buka thread di [Discussions](https://github.com/alamanda-projects/beescout/discussions) |
| Ambil item dari "Next" | Comment di issue terkait: *"Saya tertarik mengerjakan ini"*. Maintainer akan assign. |
| Pertanyakan keputusan lama | Lihat [docs/adr/](docs/adr/) — keputusan terdokumentasi di sana |

---

## English Summary

Roadmap is organized into three horizons (Now / Next / Later) plus an explicit "Not Planned" section. There are no hard deadlines — items move tiers as priorities and capacity shift. Pre-1.0; 1.0 milestone requires stable API, ≥60% test coverage, comprehensive docs, and at least 3 production deployments.
