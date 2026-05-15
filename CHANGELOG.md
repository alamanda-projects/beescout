# Changelog

Semua perubahan signifikan pada proyek BeeScout akan dicatat di file ini.

## 🛡️ Kebijakan Pembaruan

Kami mengikuti standar [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Setiap Kontributor **wajib** memperbarui file ini saat melakukan Pull Request yang menyertakan perubahan fungsional:

- Gunakan kategori: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- Sertakan tanggal dalam format `YYYY-MM-DD`.
- Deskripsikan perubahan dari sudut pandang nilai bagi pengguna/pengembang.

---

## [Unreleased]

### Added
- **Web Setup Page**: Halaman `/setup` di admin panel menggantikan `curl POST /setup` manual. Form memvalidasi password policy + memberi opsi import add-on katalog aturan & contoh kontrak.
- **Add-on Sample Contracts**: Contoh kontrak instalasi awal dipindah ke `repository/app/addons/sample_contracts/default.json`. Organisasi dapat mengganti file ini sebelum fresh install untuk membawa contoh kontrak versi internal.
- **Edit page di user panel** (#25): Halaman edit data contract kini tersedia di user panel (`/contracts/{cn}/edit`). Perubahan yang diajukan oleh `developer` / `user` otomatis masuk approval workflow — tidak langsung tersimpan.
- **Tab JSON Raw di user panel** (#25): Detail kontrak user panel kini punya tab ke-5 "JSON Raw" identik dengan admin panel.
- **Tooltip field-help di user panel** (#25, #19): Step "Struktur Data" pada form tambah/edit kontrak user panel kini punya tooltip penjelasan untuk Tipe Data Bisnis, Tipe Data Teknis, dan 4 column flags (PK, Nullable, PII, Wajib).
- **Section Koneksi (Port) di user panel** (#25): Form edit data contract user panel kini punya section Koneksi (Port) identik dengan admin panel.
- **Import YAML + Edit button di detail page user panel** (#25): Header halaman detail kontrak user panel kini punya tombol Edit dan Import YAML.

### Changed
- **Add-on Loader generalisasi**: `app/core/catalog_addon.py` di-rename ke `app/core/addon_loader.py` dan kini meng-handle dua jenis add-on (catalog rules + sample contracts) dengan helper bersama. Sample contract tidak lagi hardcoded inline di `main.py`.
- **QualityRulesEditor di user panel** (#25): Mode switch biz/eng kini aktif untuk semua user panel — `developer` default eng, `user` default biz, keduanya bisa switch. Sebelumnya locked ke biz mode.
- **Stakeholder role label di user panel** (#25, #19): Kolom Peran di halaman detail kontrak user panel kini menampilkan label cantik ("Data Owner") bukan value mentah (`owner`).
- **Constants di user panel** (#19): `CONTRACT_TYPES`, `CONSUMPTION_MODES`, `RETENTION_UNITS`, `QUALITY_DIMENSIONS` dipindah dari hardcoded inline ke export `frontend-user/src/types/contract.ts` agar sinkron dengan admin panel.

### Removed
- **Seed data legacy**: `mongo init/data-contract.js` dan `init/user.js` jadi no-op. Setup awal dilakukan via web setup page, bukan pre-seeded di volume MongoDB.
- **Setup scripts terpisah**: `scripts/install/setup.sh`, `setup.bat`, `setup-mac.command` dihapus — fungsi auto-generate `.env` dipindah ke `start.sh`/`start.bat` saat first run.

### Fixed
- **Enter key auto-submit** (#11): Form wizard Data Contract (admin + user panel) kini memblokir Enter key agar tidak men-trigger submit sebelum waktunya. Textarea dikecualikan agar navigasi multi-baris tetap berjalan normal.
- **Duplikat kontrak** (#12): Unique index MongoDB pada `contract_number` ditambahkan saat startup. Backend mengembalikan HTTP 409 jika contract number sudah digunakan — pre-check via `find_one` + `DuplicateKeyError` catch.
- **Redirect & feedback pasca simpan** (#13): Setelah kontrak berhasil disimpan, aplikasi menampilkan `toast.success` dan langsung redirect ke halaman detail kontrak yang baru dibuat.
- **Script deduplifikasi data lama** (`repository/scripts/dedupe_contracts.py`): Tersedia untuk membersihkan data duplikat yang terlanjur masuk sebelum unique index diterapkan.

---

## [1.5.0] - 2024-05-02

### Added
- **Modular Architecture**: Pemisahan repository menjadi backend (FastAPI), frontend-user (Next.js), dan frontend-admin (Next.js).
- **Approval Workflow**: Sistem voting/approval untuk perubahan Data Contract yang diajukan oleh non-admin.
- **Rule Catalog**: Katalog terpusat untuk aturan kualitas data dengan dukungan built-in rules.
- **YAML Import & Validation**: Kemampuan import kontrak via YAML dengan validasi skema ODCS.
- **Nginx Reverse Proxy**: Gateway terpusat dengan dukungan rate limiting dan IP restriction.
- **Makefile**: Otomasi workflow pengembangan (setup, up, dev, test).
- **Service Account Keys**: Dukungan kunci akses programatik untuk role `developer`.

### Changed
- Migrasi frontend ke Next.js 15 (App Router).
- Pembaruan skema Data Contract mengikuti standar ODCS yang lebih ketat.
- Peningkatan keamanan pada endpoint `/setup` untuk bootstrap root user.

### Fixed
- Perbaikan isu CORS pada deployment multi-domain.
- Optimasi performa query MongoDB pada pencarian kontrak real-time.
