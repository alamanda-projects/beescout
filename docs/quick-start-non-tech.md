# Panduan Cepat — Untuk Pengguna Non-Teknis

> Panduan ini ditujukan untuk Anda yang ingin **mencoba BeeScout di laptop sendiri** tanpa harus paham terminal, Docker, atau bahasa pemrograman. Cukup ikuti langkah-langkah di bawah — tidak perlu paham apa yang terjadi di balik layar.

Total waktu: **±20-30 menit** (sebagian besar adalah menunggu download).

---

## Apa yang Anda butuhkan

| Hal | Keterangan |
|---|---|
| **Laptop** | Mac, Windows, atau Linux. Minimal 8 GB RAM, 10 GB disk kosong. |
| **Internet** | Hanya untuk download pertama kali (±2 GB). |
| **Waktu** | 20-30 menit untuk setup pertama. Setelah itu hanya hitungan detik. |

Anda **tidak** perlu:
- Punya akun GitHub / cloud apapun
- Paham coding
- Setup database manual

---

## Langkah 1 — Install Docker Desktop

Docker adalah "wadah" yang menjalankan semua komponen BeeScout secara otomatis. Anda hanya perlu install sekali.

### Mac

1. Buka https://www.docker.com/products/docker-desktop/
2. Klik tombol **"Download for Mac"** (pilih chip yang sesuai: Apple Silicon untuk M1/M2/M3, Intel untuk Mac lama)
3. Buka file `.dmg` yang terdownload, drag ikon **Docker** ke folder **Applications**
4. Buka Docker dari folder Applications
5. Tunggu sampai ikon whale (🐳) di status bar atas berhenti berkedip — itu tandanya Docker siap

### Windows

1. Buka https://www.docker.com/products/docker-desktop/
2. Klik **"Download for Windows"**
3. Jalankan installer `Docker Desktop Installer.exe`, ikuti instruksi default (centang WSL 2 jika ditanyakan)
4. Restart laptop setelah install selesai
5. Buka Docker Desktop, tunggu sampai status **"Engine running"** di pojok kiri bawah

### Linux

Ikuti petunjuk resmi: https://docs.docker.com/engine/install/

---

## Langkah 2 — Download Folder BeeScout

Pilih salah satu cara:

### Cara A — Download ZIP (paling mudah)

1. Buka halaman repo BeeScout di GitHub
2. Klik tombol hijau **"Code"** → **"Download ZIP"**
3. Extract file zip ke folder yang mudah dicari, misal:
   - Mac/Linux: `~/Documents/beescout`
   - Windows: `C:\Users\NamaAnda\Documents\beescout`

### Cara B — Git Clone (jika punya Git)

```bash
git clone <url-repo> beescout
```

---

## Langkah 3 — Klik Setup Wizard

Buka folder BeeScout di File Explorer / Finder, masuk ke folder `scripts` → `install`. Lalu **klik dua kali** file berikut sesuai sistem operasi Anda:

| Sistem Operasi | File |
|---|---|
| **Mac** | `setup-mac.command` |
| **Windows** | `setup.bat` |
| **Linux** | Buka Terminal di folder repo, ketik: `bash scripts/install/setup.sh` |

> **Catatan Mac**: Saat pertama kali klik `.command`, mungkin muncul peringatan keamanan macOS. Solusinya: klik kanan file → **Open** → klik **Open** di dialog yang muncul.
>
> **Catatan Windows**: Mungkin muncul peringatan "Windows protected your PC". Klik **More info** → **Run anyway**.

Wizard akan otomatis:

1. ✅ Mengecek Docker terinstall dan jalan
2. ✅ Membuat file konfigurasi `.env` (lengkap dengan password yang di-generate otomatis)
3. ✅ Download dan menjalankan semua komponen (5-15 menit di first run — sambil nunggu, boleh minum kopi ☕)
4. ✅ Memandu Anda mengupdate file `hosts`

Setelah wizard selesai, Anda akan melihat pesan:

```
Selesai! 🎉
Buka browser:
  Aplikasi User  → http://app.localhost
  Panel Admin    → http://admin.localhost
```

---

## Langkah 4 — Buat Akun Super Admin Pertama

Saat pertama kali buka http://admin.localhost, **belum ada akun**. Buat akun Super Admin dengan langkah berikut:

### Cara mudah (via Terminal/Command Prompt)

Buka Terminal (Mac/Linux) atau Command Prompt (Windows), copy-paste perintah ini, **ganti `password` dengan password kuat pilihan Anda**:

**Mac / Linux:**
```bash
curl -X POST http://app.localhost/api/setup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "superadmin",
    "password": "Ganti_Password_Kuat_123!",
    "name": "Super Administrator",
    "group_access": "root",
    "data_domain": "all",
    "is_active": true
  }'
```

**Windows (PowerShell):**
```powershell
curl -Method POST -Uri http://app.localhost/api/setup `
  -ContentType "application/json" `
  -Body '{"username":"superadmin","password":"Ganti_Password_Kuat_123!","name":"Super Administrator","group_access":"root","data_domain":"all","is_active":true}'
```

> **Aturan password**: minimal 8 karakter, harus mengandung huruf besar, huruf kecil, angka, dan karakter khusus.

Setelah berhasil, login ke http://admin.localhost dengan username & password tadi.

---

## Pemakaian Sehari-hari

Setelah setup selesai, untuk pemakaian harian Anda hanya butuh 2 file:

| Aktivitas | Mac | Windows | Linux |
|---|---|---|---|
| Mulai BeeScout | klik `start-mac.command` | klik `start.bat` | `bash scripts/install/start.sh` |
| Matikan BeeScout | klik `stop-mac.command` | klik `stop.bat` | `bash scripts/install/stop.sh` |

> Tidak perlu jalankan `setup` lagi — itu hanya untuk pertama kali.

**Tip**: Anda bisa **drag** file `.command` (Mac) atau `.bat` (Windows) ke Desktop untuk akses cepat.

---

## Mematikan & Menghidupkan Lagi

- **Mematikan**: data Anda **tidak hilang**, hanya layanan dihentikan. Saat hidup lagi, semua data kontrak tetap ada.
- **Menghidupkan kembali setelah restart laptop**: Docker Desktop biasanya auto-start. Jika tidak, buka Docker Desktop manual, tunggu siap, lalu klik `start-mac.command` / `start.bat`.

---

## Kalau Ada Masalah

### "Docker belum jalan"
- Buka aplikasi **Docker Desktop**
- Tunggu sampai ikon whale di status bar berhenti berkedip (Mac) atau status "Engine running" (Windows)
- Klik script setup/start lagi

### Browser bilang "This site can't be reached"
- Pastikan file `hosts` sudah diupdate (lihat Langkah 4 wizard)
- Pastikan layanan jalan — cek dengan klik kanan ikon Docker → Dashboard, lihat ada 5 container berstatus **running**:
  - `beescout-nginx-1`
  - `beescout-backend-1`
  - `beescout-frontend-user-1`
  - `beescout-frontend-admin-1`
  - `beescout-db-1`

### Setup gagal di tengah jalan
- Buka Terminal/Command Prompt, masuk ke folder beescout, jalankan: `docker compose down`
- Hapus file `.env` (jika dibuat)
- Klik wizard setup lagi dari awal

### Disk hampir penuh
- Buka Docker Desktop → Settings → Resources → Disk image size — cek pemakaian
- Jalankan di Terminal: `docker system prune -f` (akan hapus image lama yang tidak terpakai)

### Lupa password Super Admin
- Akun tersimpan di MongoDB. Hubungi developer/admin untuk reset, atau buat ulang dengan menghapus volume data:
  ```bash
  docker compose down -v   # ⚠️ menghapus SEMUA data kontrak!
  ```
  Lalu jalankan wizard setup lagi.

---

## Pertanyaan Umum

**Q: Apakah data saya kirim ke internet?**
A: Tidak. Semua data tersimpan di laptop Anda (di volume Docker). BeeScout tidak konek ke server eksternal.

**Q: Bisakah saya pakai untuk produksi/perusahaan?**
A: Untuk dev lokal: ya, langsung pakai. Untuk produksi: konsultasi dengan tim IT — perlu setup HTTPS, domain asli, backup MongoDB, dll. Lihat [getting-started.md](../getting-started.md).

**Q: Bagaimana cara update ke versi baru?**
A: Download ulang folder ZIP terbaru, copy folder `.env` lama ke folder baru, klik `setup` lagi (akan deteksi `.env` sudah ada dan tidak menimpa).

**Q: Bagaimana cara backup data saya?**
A: Data MongoDB ada di volume Docker. Untuk backup, jalankan:
```bash
docker exec beescout-db-1 mongodump --uri="mongodb://admin:password@localhost:27017/dgrdb?authSource=admin" --out=/tmp/backup
docker cp beescout-db-1:/tmp/backup ./mongo-backup
```
Ganti `password` dengan `MONGODB_PASS` di file `.env` Anda.

---

## Butuh Bantuan Lebih Lanjut?

- Panduan lengkap (untuk developer): [getting-started.md](../getting-started.md)
- Persona pengguna: [docs/personas.md](personas.md)
- Glosarium istilah: [docs/glossary.md](glossary.md)
- Laporkan bug: [GitHub Issues](https://github.com/alamanda-projects/beescout/issues)
