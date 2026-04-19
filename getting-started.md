# Getting Started — BeeScout

Panduan lengkap untuk menjalankan BeeScout dari nol, baik untuk pengembangan lokal maupun deployment produksi.

---

## Prasyarat

| Tools | Versi Minimum |
|---|---|
| Docker | 24.x |
| Docker Compose | v2.x (`docker compose`, bukan `docker-compose`) |
| Make | opsional, memudahkan perintah |
| Node.js | 20.x (hanya jika dev frontend tanpa Docker) |

---

## 1. Clone & Setup

```bash
git clone <url-repo> beescout
cd beescout
```

Salin template environment:

```bash
cp .env.example .env
```

Edit `.env` — bagian yang **wajib** diubah:

```env
# Domain — tambahkan ke /etc/hosts untuk dev lokal
BEESCOUT_USER_DOMAIN=app.localhost
BEESCOUT_ADMIN_DOMAIN=admin.localhost

# Database
MONGODB_USER=admin
MONGODB_PASS=ganti_dengan_password_kuat

# JWT secrets — generate dengan: openssl rand -hex 32
TKN_SECRET_KEY=...
TKN_SECRET_TOKEN=...
SA_SECRET_KEY=...
SA_SECRET_TOKEN=...

# CORS — sesuaikan dengan domain yang dipakai
ALLOWED_ORIGINS=http://app.localhost,http://admin.localhost
```

---

## 2. Jalankan Full Stack

```bash
make up
# atau: docker compose up --build -d
```

Lima container akan berjalan:

| Container | Fungsi | Port (internal) |
|---|---|---|
| `nginx` | Reverse proxy, security gateway | 80 (host) |
| `backend` | FastAPI REST API | 8888 |
| `frontend-user` | Aplikasi untuk user & developer | 3000 |
| `frontend-admin` | Panel admin (admin & root) | 3001 |
| `db` | MongoDB (hanya di internal network) | 27017 |

```bash
make status    # cek status semua container
make logs      # lihat log real-time
```

---

## 3. Konfigurasi `/etc/hosts` (dev lokal)

Tambahkan baris berikut ke `/etc/hosts` (Mac/Linux):

```
127.0.0.1   app.localhost
127.0.0.1   admin.localhost
```

Kemudian buka di browser:

- **User App** → http://app.localhost
- **Admin Panel** → http://admin.localhost

---

## 4. Buat Akun Pertama (Super Admin)

Gunakan endpoint `/setup` yang hanya aktif saat belum ada akun root:

```bash
# Cek apakah setup sudah dilakukan
curl http://app.localhost/api/setup/status
# {"setup_complete": false}  ← belum ada root, lanjutkan

# Buat akun root pertama
curl -X POST http://app.localhost/api/setup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "superadmin",
    "password": "Admin@1234!",
    "name": "Super Administrator",
    "group_access": "root",
    "data_domain": "all",
    "is_active": true
  }'
```

Setelah berhasil, endpoint `/setup` akan mengembalikan `409` jika dipanggil lagi — akun root sudah terlindungi. Login via Admin Panel, lalu buat user tambahan dari menu **Manajemen User**.

> Password harus mengandung huruf besar, kecil, angka, dan karakter khusus (minimal 8 karakter).

---

## 5. Fitur Frontend — User App (`app.localhost`)

Aplikasi untuk pengguna dengan role `user` dan `developer`.

### Halaman Login
- Form login dengan validasi Zod
- Error toast jika kredensial salah
- Auto-redirect ke dashboard setelah berhasil
- Middleware route guard — semua halaman terlindungi

### Dashboard
- Statistik ringkasan: total kontrak, jumlah pemilik, jumlah tipe
- Tabel kontrak terbaru (6 data terakhir)
- Tombol navigasi cepat ke halaman Data Contract

### Data Contract
- Tabel daftar kontrak dengan kolom: Nama, Nomor, Pemilik, Tipe, Versi
- Pencarian real-time (filter nama, nomor kontrak, pemilik, tipe)
- Klik nama/panah untuk membuka detail kontrak

### Detail Kontrak (4 Tab)
| Tab | Konten |
|---|---|
| **Informasi** | Nama, pemilik, tipe, versi, SLA, daftar stakeholders |
| **Struktur Data** | Tabel kolom: nama, tipe logis, flag PK/PII/wajib/nullable |
| **Koneksi** | Port dan properti koneksi data |
| **Contoh Data** | Preview data contoh dalam format JSON |

### Profil
- Informasi akun: username, peran, domain, tipe akun
- Status akun aktif/nonaktif
- Daftar Service Account Keys (untuk role `developer`): client ID, tanggal buat, tanggal kedaluwarsa, status

---

## 6. Fitur Frontend — Admin Panel (`admin.localhost`)

Aplikasi untuk pengguna dengan role `admin` dan `root`. Memiliki guard tambahan di sisi server — akses non-admin langsung ditolak dengan halaman "Akses Ditolak".

### Halaman Login
- Tampilan dark theme dengan branding "Portal Administrasi — Akses Terbatas"
- Validasi client-side + pesan error dari server

### Dashboard Admin
- Statistik: total kontrak, jumlah pemilik, jumlah tipe kontrak
- Tabel kontrak terbaru (6 data) dengan nama, pemilik, tipe
- Tombol aksi cepat: Tambah Kontrak, Lihat Semua

### Data Contract (Daftar)
- Tabel lengkap semua kontrak lintas domain
- Pencarian real-time: nama, nomor kontrak, pemilik, tipe
- Badge tipe berwarna (dataset/api/stream/report/model)
- Navigasi ke halaman detail atau tambah kontrak baru

### Detail Kontrak (5 Tab)
| Tab | Konten |
|---|---|
| **Informasi** | Metadata lengkap: nama, pemilik, tipe, versi, SLA, stakeholders |
| **Struktur Data** | Tabel kolom dengan ikon centang/silang untuk setiap flag |
| **Koneksi** | Daftar port beserta properti masing-masing |
| **Contoh Data** | JSON preview data contoh |
| **JSON Raw** | Full raw JSON kontrak untuk debugging |

### Tambah Kontrak Baru (Multi-Step Form)

Form dibagi menjadi 4 langkah dengan indikator progres:

```
Step 1 ──── Step 2 ──── Step 3 ──── Step 4
Informasi   SLA &       Struktur    Tinjauan
Dasar       Pemangku    Data        & Simpan
```

**Step 1 — Informasi Dasar**
- Nomor kontrak (auto-generate dari backend atau input manual)
- Versi standar, versi kontrak
- Tipe kontrak: dataset / api / stream / report / model
- Nama, pemilik, mode konsumsi
- Deskripsi: tujuan dan cara penggunaan

**Step 2 — SLA & Pemangku Kepentingan**
- SLA: ketersediaan, frekuensi pembaruan, retensi data, jadwal cron
- Stakeholders: tambah/hapus dinamis (nama, peran, email)

**Step 3 — Struktur Data & Koneksi**
- Definisi kolom: tambah/hapus dinamis dengan field nama kolom, nama bisnis, tipe logis, deskripsi, dan flag (PK, nullable, PII, wajib)
- Port koneksi: tambah/hapus dengan nama objek dan properties key-value

**Step 4 — Tinjauan**
- Preview lengkap semua data yang diisi dalam format JSON
- Tombol Submit untuk menyimpan ke backend

### Manajemen User
- Form buat user baru: username, nama lengkap, password (validasi kuat), peran, domain data, status aktif
- Indikator akses: hanya role `root` yang bisa submit; tombol dinonaktifkan untuk role lain
- Banner peringatan jika akun bukan Super Admin
- Notifikasi sukses setelah user berhasil dibuat

### Profil Admin
- Informasi akun: username, peran, domain, tipe akun, status aktif/nonaktif
- Avatar dengan inisial
- Badge peran dan status
- Tabel Service Account Keys (jika ada)

### Header & Navigasi
- Sidebar gelap dengan logo BeeScout dan label "Panel Admin"
- Menu navigasi: Dashboard, Data Contract, Tambah Kontrak, Manajemen User, Profil
- Header: badge "Admin Portal", dropdown user (nama, peran, domain) dengan menu Profil dan Keluar

---

## 7. Mode Development (tanpa rebuild Docker)

```bash
# Jalankan stack dev — port lebih terbuka, hot reload
make dev
```

Atau jalankan frontend lokal sambil backend tetap di Docker:

```bash
# Terminal 1 — Backend + DB saja
make up-be

# Terminal 2 — Frontend User (port 3000)
cd frontend-user
cp .env.example .env.local
# Edit: NEXT_PUBLIC_API_BASE=http://localhost:8888
npm install && npm run dev

# Terminal 3 — Frontend Admin (port 3001)
cd frontend-admin
cp .env.example .env.local
# Edit: NEXT_PUBLIC_API_BASE=http://localhost:8888
npm install && npm run dev
```

---

## 8. Perintah Berguna

```bash
make setup        # copy .env.example → .env
make up           # build & jalankan full stack
make down         # stop semua container
make restart      # restart semua container
make logs         # lihat log semua container (real-time)
make status       # lihat status semua container
make dev          # jalankan mode development
make dev-down     # stop dev stack
make up-be        # jalankan backend + db saja
make test         # jalankan semua tests (backend + TS typecheck)
make test-backend # pytest untuk backend saja
make test-fe-admin # TypeScript check untuk frontend-admin
make test-fe-user  # TypeScript check untuk frontend-user
```

---

## 9. Health Check

```bash
curl http://app.localhost/api/health
# {"status": "ok", "service": "BeeScout Repository"}
```

---

## 10. Troubleshooting

**Container tidak bisa start**
```bash
docker compose logs backend   # error backend
docker compose logs nginx     # error nginx config
```

**Port 80 sudah terpakai**  
Edit `docker-compose.yml`, ganti `"80:80"` ke `"8080:80"`. Akses via `http://app.localhost:8080`.

**CORS error di browser**  
Pastikan `ALLOWED_ORIGINS` di `.env` mencakup domain yang dipakai:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

**MongoDB connection failed**  
Pastikan `MONGODB_USER`, `MONGODB_PASS`, `MONGODB_DB` di `.env` sudah benar dan container `db` berstatus `running`.

**Akses ditolak di Admin Panel**  
Akun harus memiliki role `admin` atau `root`. Login sebagai akun biasa akan menampilkan halaman "Akses Ditolak" dan tidak bisa masuk ke dashboard admin.
