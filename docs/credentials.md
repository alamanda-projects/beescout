# Kredensial & Keamanan Pengembangan

Halaman ini merangkum kredensial bawaan yang digunakan selama pengembangan lokal (development).

> [!CAUTION]
> **JANGAN PERNAH** menggunakan kredensial ini di lingkungan produksi. Selalu inisialisasi akun root Anda sendiri melalui endpoint `/setup`.

## 👤 Akun Bawaan (Default Users)

| Username | Password | Role | Data Domain | Keterangan |
|---|---|---|---|---|
| `root` | `@DM1Nyellow` | `root` | `root` | Superuser dengan akses penuh |
| `admin` | `admiN!23` | `admin` | `admin` | Admin untuk manajemen kontrak |
| `user` | `useR!234` | `user` | `penjualan` | Pengguna biasa (read-only) |
| `da` | `useR!234` | `user` | `inventory` | Data Analyst |
| `ae` | `deveL!234` | `developer` | `penjualan` | Analytic Engineer |

## 🔑 Inisialisasi Produksi

Untuk setup awal di server baru, BeeScout menyediakan endpoint bootstrap:

1. Pastikan database kosong atau belum ada user root.
2. Panggil endpoint `/setup` (hanya bisa sekali):
   ```bash
   curl -X POST http://your-domain.com/api/setup \
     -H "Content-Type: application/json" \
     -d '{
       "username": "your_admin",
       "password": "StrongPassword123!",
       "name": "Admin Name",
       "group_access": "root",
       "data_domain": "all",
       "is_active": true
     }'
   ```

## 🔐 Environment Variables (.env)

Pastikan rahasia JWT diganti dengan nilai random yang kuat:
```env
TKN_SECRET_KEY=openssl rand -hex 32
SA_SECRET_KEY=openssl rand -hex 32
MONGODB_PASS=GantiDenganPasswordKuat
```
