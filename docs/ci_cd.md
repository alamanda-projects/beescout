# CI/CD & Testing

BeeScout menggunakan alur kerja otomatis untuk memastikan kualitas kode dan stabilitas sistem sebelum perubahan digabungkan ke branch utama.

## 🧪 Testing Lokal

Sangat disarankan untuk menjalankan test secara lokal sebelum membuat Pull Request.

### Backend (Python/FastAPI)
Menggunakan `pytest` dan `httpx` untuk simulasi API calls.
```bash
make test-backend
```

### Frontend (Next.js/TypeScript)
Menggunakan `tsc` untuk pengecekan tipe statis.
```bash
make test-fe-admin
make test-fe-user
```

### Full Test Suite
Menjalankan semua test backend dan frontend sekaligus.
```bash
make test
```

## 🚀 GitHub Actions

Setiap Push dan Pull Request ke branch `main` akan memicu workflow otomatis:
1. **Linting**: Pengecekan gaya penulisan kode.
2. **Testing**: Menjalankan seluruh test suite di lingkungan Docker terisolasi.
3. **Build Check**: Memastikan Docker image dapat di-build tanpa error.

## 🛠️ Linting & Formatting

Kami menggunakan:
- **Backend**: `flake8` atau `ruff` (cek `Makefile`).
- **Frontend**: `eslint` dan `prettier`.

Pastikan tidak ada error linting dengan menjalankan:
```bash
# Menjalankan linting (jika dikonfigurasi di Makefile)
make lint
```
