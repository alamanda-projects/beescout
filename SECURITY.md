# Kebijakan Keamanan

Terima kasih telah membantu menjaga keamanan **BeeScout** dan penggunanya.

## Versi yang Didukung

BeeScout masih dalam pengembangan aktif (pre-1.0). Patch keamanan akan diterapkan pada **branch `main`** terbaru. Pengguna sangat disarankan selalu memakai rilis terbaru.

| Versi | Status Dukungan |
|---|---|
| `main` (HEAD) | ✅ Didukung penuh |
| Tag rilis < 1.0 | ⚠️ Best-effort, tidak ada SLA |

## Cara Melaporkan Kerentanan

**Jangan** membuat issue publik untuk masalah keamanan. Hal ini dapat memberi penyerang keuntungan sebelum perbaikan tersedia.

Gunakan salah satu jalur privat berikut:

1. **GitHub Security Advisory** *(disarankan)*
   Buka tab **Security** di repo → klik **Report a vulnerability**.
   Ini menjaga laporan tetap privat sampai patch dirilis.

2. **Email langsung** ke maintainer
   Hubungi [Hani Perkasa via LinkedIn](https://www.linkedin.com/in/haninp/) untuk meminta alamat email keamanan.

### Yang sebaiknya dicantumkan dalam laporan

- Deskripsi singkat kerentanan dan dampaknya
- Langkah reproduksi (kode, request, atau skenario)
- Versi/commit yang terkena dampak
- Saran mitigasi atau patch (opsional)
- Apakah Anda ingin diakui di rilis catatan (opsional)

## Komitmen Respon

| Tahap | Target Waktu |
|---|---|
| Konfirmasi penerimaan laporan | **3 hari kerja** |
| Penilaian awal & kategorisasi severity | **7 hari kerja** |
| Patch untuk severity Critical/High | **30 hari** dari konfirmasi |
| Patch untuk severity Medium/Low | Best-effort, biasanya pada rilis berikutnya |
| Pengumuman publik | Setelah patch tersedia, dengan kredit kepada pelapor (jika diizinkan) |

Karena BeeScout dipelihara komunitas kecil (lihat [GOVERNANCE.md](GOVERNANCE.md)), kami akan transparan jika ada keterlambatan.

## Cakupan

**In-scope** (silakan laporkan):
- Backend FastAPI (`repository/app/`)
- Frontend admin & user (`frontend-admin/`, `frontend-user/`)
- Konfigurasi Nginx (`nginx/templates/`)
- Konfigurasi Docker (`docker-compose*.yml`, `Dockerfile`)
- Skema database & validasi input (Pydantic models)
- Kerentanan logika bisnis (mis. bypass approval, escalasi role)

**Out-of-scope** (umumnya tidak dianggap kerentanan):
- Kerentanan di dependensi pihak ketiga — laporkan ke upstream-nya. Kami akan update saat patch tersedia.
- Konfigurasi default `.env.example` yang memang dimaksudkan untuk dev lokal (`MONGODB_PASS=changeme_strong_password_here`, `COOKIE_SECURE=false`, dll). Dokumentasi sudah memperingatkan untuk diganti di production.
- Denial-of-service yang membutuhkan resource ekstrem
- Self-XSS atau yang membutuhkan akses fisik ke device korban
- Praktik terbaik (best practice) yang tidak menghasilkan dampak konkret

## Catatan Lisensi (AGPL-3.0)

BeeScout dirilis di bawah **AGPL-3.0**. Implikasinya:

- Jika Anda meng-host atau mendeploy versi modifikasi BeeScout sebagai layanan kepada pengguna lain (termasuk penggunaan internal lintas-organisasi), Anda **wajib** menyediakan source code modifikasi tersebut kepada pengguna layanan.
- Jika Anda menemukan vulnerability di fork yang dideploy publik dan fork tersebut tidak menyediakan source code, kami menyarankan Anda menghubungi operator fork terlebih dahulu, lalu melaporkan kepada kami sebagai informasi.

## Hall of Fame

Daftar pelapor yang telah membantu meningkatkan keamanan BeeScout akan dicantumkan di [CHANGELOG.md](CHANGELOG.md) (jika diizinkan).

---

## English Summary

Report vulnerabilities **privately** via GitHub Security Advisory or by contacting the maintainer through [LinkedIn](https://www.linkedin.com/in/haninp/). Do not file public issues for security matters.

We aim to acknowledge reports within 3 business days, assess within 7, and patch Critical/High issues within 30 days. BeeScout is licensed under AGPL-3.0 — modifications deployed as a network service must publish their source.
