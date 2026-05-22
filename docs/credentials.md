# Kredensial & Keamanan Pengembangan

Halaman ini merangkum kredensial bawaan yang digunakan selama pengembangan lokal (development).

> [!CAUTION]
> **JANGAN PERNAH** menggunakan kredensial legacy ini di lingkungan produksi. Selalu buat akun root pertama melalui halaman setup web.

## 👤 Akun Bawaan Lama (Development Legacy)

Fresh install tidak lagi membuat akun bawaan otomatis. Akun Super Admin pertama dibuat melalui halaman setup web.

| Username | Password | Role | Data Domain | Keterangan |
|---|---|---|---|---|
| `root` | `@DM1Nyellow` | `root` | `root` | Hanya ada pada volume/data development lama |
| `admin` | `admiN!23` | `admin` | `admin` | Admin untuk manajemen kontrak |
| `user` | `useR!234` | `user` | `penjualan` | Pengguna biasa (read-only) |
| `da` | `useR!234` | `user` | `inventory` | Data Analyst |
| `ae` | `deveL!234` | `developer` | `penjualan` | Analytic Engineer |

## 🔑 Inisialisasi Produksi

Untuk setup awal di server baru, gunakan halaman setup web:

```text
https://admin.yourcompany.com/setup
```

Halaman ini hanya dapat dipakai saat database belum memiliki akun root aktif. Untuk instalasi produksi yang bersih, biarkan opsi import contoh Data Contract tidak dicentang. Opsi import add-on katalog aturan kualitas bawaan boleh tetap aktif jika organisasi belum memiliki add-on aturan sendiri.

## 🔐 Environment Variables (.env)

Pastikan rahasia JWT diganti dengan nilai random yang kuat:
```env
TKN_SECRET_KEY=openssl rand -hex 32
SA_SECRET_KEY=openssl rand -hex 32
MONGODB_PASS=GantiDenganPasswordKuat
```

## 🔁 Rotasi Secret (Production)

Rotasi secret diperlukan secara berkala dan **wajib segera** bila ada dugaan
kebocoran. Semua secret hidup di `.env` server — tidak ada di source.

| Secret | Dampak rotasi |
|---|---|
| `TKN_SECRET_KEY` / `TKN_SECRET_TOKEN` | Semua sesi user ter-invalidasi — user harus login ulang |
| `SA_SECRET_KEY` / `SA_SECRET_TOKEN` | Semua service-account key lama tidak valid — perlu generate ulang |
| `MONGODB_PASS` | Harus diganti di MongoDB **dan** `.env` secara bersamaan |

### Prosedur — JWT / SA secret

```bash
# 1. Generate nilai baru (jalankan per key, nilai harus berbeda)
openssl rand -hex 32

# 2. Update .env di server dengan nilai baru
# 3. Terapkan — restart backend
docker compose up -d backend

# 4. Verifikasi: sesi lama tertolak, login baru berhasil
```

### Prosedur — MongoDB password

```bash
# 1. Ganti password user di MongoDB
docker exec beescout-db-1 mongosh \
  "mongodb://$OLD_USER:$OLD_PASS@localhost:27017/admin?authSource=admin" \
  --eval 'db.changeUserPassword("'"$MONGODB_USER"'", "PASSWORD_BARU")'

# 2. Update MONGODB_PASS di .env
# 3. Restart backend agar konek dengan kredensial baru
docker compose up -d backend
```

### Aturan

- Satu secret = satu nilai unik. **Jangan** pakai nilai yang sama untuk
  `*_KEY` dan `*_TOKEN`.
- Simpan secret di password manager / vault, bukan email/chat.
- Setelah rotasi, hapus nilai lama dari vault.
- Catat tanggal rotasi terakhir di runbook internal.

Lihat juga [deploy-production.md](deploy-production.md) untuk checklist go-live lengkap.
