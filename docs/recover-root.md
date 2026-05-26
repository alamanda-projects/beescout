# Pemulihan Akun Root (Break-Glass)

> ⚠️ **Bukan alat sehari-hari.** Ini prosedur darurat. Untuk ganti password biasa, login → halaman **Profil**.
>
> ⚠️ **Memerlukan akses shell ke server — tidak ada UI.** Kalau Anda hosting di managed/shared environment tanpa shell, prosedur ini tidak applicable.
>
> ⚠️ **Selalu dry-run dulu.** Baca rencananya sebelum menambahkan `--apply`.

---

## Apa itu "break-glass"

Istilah dari physical security: kotak alarm kebakaran yang **harus dipecahkan kacanya** untuk diakses. Dalam konteks software, "break-glass procedure" adalah prosedur darurat yang:

- Melewati alur otentikasi/otorisasi normal
- Memerlukan akses langsung ke server atau database
- Meninggalkan jejak audit yang jelas
- Tidak dipakai dalam operasi harian

Script [`repository/scripts/recover_root.py`](../repository/scripts/recover_root.py) adalah break-glass tool BeeScout untuk akun root.

---

## Kapan menggunakannya

Tiga skenario sah:

1. **Lupa password akun root**, akun masih ada di DB
2. **Tidak ada root aktif** (semua dokumen root punya `is_active=false`) — `/setup` tetap menolak dengan 409
3. **Restore backup / DB lama** yang tidak punya dokumen root sama sekali

## Kapan **TIDAK** menggunakannya

| Situasi | Pakai ini |
|---|---|
| Seed instance baru (belum ada root sama sekali) | `SEED_ROOT_*` env vars (auto-seed) atau buka `/setup` di browser |
| Lupa password sendiri padahal masih bisa login | Halaman **Profil** di UI |
| Ingin bersih total (development) | `make reset-db` |
| Lupa password user non-root | Login sebagai root → halaman **Manajemen User** |

---

## Kenapa tidak ada endpoint HTTP

Karena endpoint recovery via HTTP = **pintu belakang account-takeover**. Siapa saja yang menemukan URL-nya bisa mengambil alih instance. Trust boundary yang ditegakkan di sini: **akses shell ke server / container backend**. Kalau penyerang sudah punya shell, dia sudah punya everything — recovery script tidak menambah permukaan serangan.

Detail desain: lihat docstring [`repository/scripts/recover_root.py`](../repository/scripts/recover_root.py) dan komit awal di issue #61.

---

## Step-by-step

### 1. Pastikan container backend & db berjalan

```bash
docker compose ps
```

Pastikan `beescout-backend-1` dan `beescout-db-1` berstatus `running`. Kalau tidak, jalankan dulu:

```bash
docker compose up -d backend db
```

### 2. Dry-run dulu

Dry-run **tidak menulis apa pun** ke database — hanya menampilkan rencana eksekusi.

```bash
docker compose run --rm backend python -m scripts.recover_root \
  --username root --name "Root User"
```

Output yang diharapkan:

```
=== recover_root [DRY-RUN] ===
  Mode           : recovery (reset akun ada)
  Username target: root
  Root lain      : 0 dokumen → akan di-non-aktifkan

(dry-run — tidak ada perubahan. Tambah --apply untuk eksekusi.)
```

Kalau `Root lain` > 0, perhatikan daftarnya — semua akan di-non-aktifkan untuk menjaga invariant "tepat satu root aktif" (#59).

### 3. Eksekusi dengan `--apply`

```bash
docker compose run --rm backend python -m scripts.recover_root \
  --username root --name "Root User" --apply
```

Script akan meminta password 2× tanpa echo:

```
Password root baru:
Ulangi password    :
✓ Akun root 'root' di-reset & diaktifkan.

✓ Selesai. Tepat satu root aktif: 'root'. Silakan login.
  AUDIT: break-glass via scripts.recover_root pada 2026-05-26T10:30:00
```

> 💡 **Jangan pakai `--password <plaintext>`** kalau bisa dihindari — password akan tercatat di `~/.bash_history` / `~/.zsh_history`. Biarkan script meminta lewat prompt aman.

### 4. Verifikasi via `mongosh`

Cek bahwa hanya ada satu root aktif dan field audit ter-stempel. Password MongoDB ada di `.env` sebagai `MONGODB_PASS`.

```bash
docker exec beescout-db-1 mongosh \
  "mongodb://admin:<MONGODB_PASS>@localhost:27017/dgrdb?authSource=admin" \
  --eval 'db.dgrusr.find({group_access:"root"},{username:1,is_active:1,recovered_at:1,recovery_note:1}).toArray()'
```

Harus terlihat tepat satu dokumen dengan `is_active: true` dan field `recovered_at` + `recovery_note` terisi.

### 5. Login → rotasi password lagi sebagai higiene

Login ke `http://admin.localhost` dengan password yang baru diset, lalu buka halaman **Profil** dan rotasi password sekali lagi. Alasannya: password yang baru saja Anda ketik bisa jadi sempat terlihat di sesi terminal, log, atau monitor. Rotasi cepat menutup jendela paparannya.

---

## Aturan password

Identik dengan `/setup` dan `/user/create`:

- Minimal **8 karakter**
- Wajib ada huruf **besar**, huruf **kecil**, **angka**, dan **karakter khusus**
- Karakter khusus yang diterima: `` !@#$%^&*()-_+={}[]<>,./?;:'" ``

Kalau password ditolak, dry-run/eksekusi berhenti dengan pesan jelas.

---

## Jejak audit

Setiap eksekusi `--apply` meninggalkan jejak berikut:

| Lokasi | Apa yang tercatat |
|---|---|
| Dokumen user di MongoDB | `recovered_at` (timestamp ISO), `recovery_note` (string "break-glass via scripts.recover_root pada \<timestamp>") |
| Log Docker | Ringkasan rencana + line `AUDIT: ...` di akhir |

Jangan hapus field `recovered_at` / `recovery_note` — itu satu-satunya jejak bahwa akun pernah di-reset out-of-band.

---

## FAQ

### Apa beda dengan `SEED_ROOT_*` env vars?

`SEED_ROOT_*` jalan otomatis saat **container backend start** dan hanya membuat root pertama kalau **belum ada root** sama sekali. Cocok untuk first-run deploy. Recovery script jalan **manual on-demand** dan bekerja meski sudah ada root (dengan mode recovery). Keduanya bisa digunakan bersamaan tanpa konflik.

### Apa yang terjadi pada akun root lain?

Semua dokumen root selain target akan di-set `is_active=false`. Ini menjaga invariant "tepat satu root aktif" (#59). Dokumen tidak dihapus — hanya dinonaktifkan, jadi bisa dilihat di MongoDB untuk audit/forensik.

### Bagaimana kalau lupa password MongoDB juga?

Game over untuk data — recovery script tidak bisa connect tanpa kredensial DB. Pilihannya:

1. Cari `.env` yang masih punya `MONGODB_PASS` (backup, server lain, password manager)
2. Kalau benar-benar hilang: `make reset-db` (nuklir — semua data terhapus, mulai dari nol)

Tidak ada jalan tengah. MongoDB-nya adalah trust root paling bawah.

### Bisa pakai `--password` untuk automation?

Bisa, tapi password akan tercatat di shell history dan mungkin di proses listing (`ps aux`). Kalau benar-benar perlu untuk automation: gunakan environment variable + `printf` ke stdin, atau jalankan dari Python wrapper. Untuk pemakaian manusia, biarkan prompt.

---

## Lihat juga

- [CLAUDE.md → Troubleshooting](../CLAUDE.md) — referensi cepat untuk AI agent & developer
- [`repository/scripts/recover_root.py`](../repository/scripts/recover_root.py) — source code (docstring detail desain)
- [`repository/tests/test_recover_root.py`](../repository/tests/test_recover_root.py) — invariant yang dijamin
- Issue [#59](https://github.com/alamanda-projects/beescout/issues/59) — single-active-root invariant
- Issue [#61](https://github.com/alamanda-projects/beescout/issues/61) — desain awal break-glass
