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
