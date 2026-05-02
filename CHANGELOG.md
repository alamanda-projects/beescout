# Changelog

Semua perubahan signifikan pada proyek BeeScout akan dicatat di file ini.

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
