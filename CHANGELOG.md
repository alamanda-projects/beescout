# Changelog

Semua perubahan signifikan pada proyek BeeScout akan dicatat di file ini.

## 🛡️ Kebijakan Pembaruan

Kami mengikuti standar [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Setiap Kontributor **wajib** memperbarui file ini saat melakukan Pull Request yang menyertakan perubahan fungsional:

- Gunakan kategori: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- Sertakan tanggal dalam format `YYYY-MM-DD`.
- Deskripsikan perubahan dari sudut pandang nilai bagi pengguna/pengembang.

---

## [Unreleased]

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
