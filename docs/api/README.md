# BeeScout API — Postman Collection

Koleksi Postman yang auto-generated dari skema OpenAPI FastAPI BeeScout. Source of truth tetap di [`repository/app/main.py`](../../repository/app/main.py) + Pydantic models — file di sini di-regenerate, **bukan** diedit manual.

## File

| File | Isi |
|---|---|
| [`beescout.postman_collection.json`](beescout.postman_collection.json) | 47 endpoint, dikelompokkan per area (System, User, Domain, Data Contract, Approval, Catalog, YAML Import) |
| [`beescout.postman_environment.json`](beescout.postman_environment.json) | Variable: `base_url`, `username`, `password` (placeholder — ganti dengan kredensial lokal) |

## Import ke Postman

1. Buka Postman → **File → Import**
2. Drag dua file di atas ke modal Import
3. Di pojok kanan atas Postman, pilih environment **"BeeScout Local"**
4. Edit `base_url`, `username`, `password` sesuai instance Anda

## Cara login (cookie httpOnly)

Backend pakai JWT di cookie httpOnly — **bukan** Authorization header. Setelah `POST /login` berhasil, Postman otomatis menyimpan cookie `access_token` dan mengirimnya di request berikutnya.

**Alur singkat untuk eksplorasi:**

1. (Sekali saja, kalau instance baru) — jalankan `POST /setup` di folder *00. System & Bootstrap* untuk membuat root account pertama
2. Jalankan `POST /login` dengan body `{"username": "{{username}}", "password": "{{password}}"}` — cookie ter-set otomatis
3. Sekarang request ke endpoint ter-proteksi (misal `GET /datacontract/lists`) akan jalan

Kalau dapat **401**, cek tab **Cookies** di Postman — kemungkinan cookie sudah expired (JWT default 3 jam). Login ulang.

## Skenario role gating

Setiap endpoint punya `description` yang menyebutkan role yang boleh akses (`require_root`, `require_admin`, `require_any`, atau scope-based). Untuk menguji role berbeda:

1. Buat akun di `POST /user/create` (sebagai root/admin) dengan `group_access` yang ingin diuji
2. Logout (`POST /logout`)
3. Login ulang dengan akun baru
4. Coba endpoint yang ingin diuji — harus dapat 403 untuk yang tidak ter-otorisasi

| Role | Bisa akses |
|---|---|
| `root` | semua |
| `admin` | semua kecuali user-management mutasi (`PATCH /user/{username}`, `DELETE /user/{username}`) |
| `developer` | sub-set + bisa generate SA key |
| `user` | sub-set, read-only mostly |

Detail lengkap: [`CLAUDE.md` — Quick reference: Access Levels](../../CLAUDE.md).

## Regenerate (untuk kontributor)

Setiap kali ada perubahan endpoint backend (route baru, ganti method/path, ganti request/response body, atau hapus endpoint), regenerate collection:

```bash
make regen-postman
```

Lalu commit file `docs/api/beescout.postman_collection.json` yang berubah. CLAUDE.md "Definition of Done" mewajibkan langkah ini di setiap PR yang menyentuh API.

Script generator: [`repository/scripts/gen_postman.py`](../../repository/scripts/gen_postman.py).

## Catatan implementasi

- **Body contoh** dibangun dari JSON Schema (Pydantic model) — field-nya berisi placeholder per-type. Edit sesuai data nyata sebelum kirim.
- **Path params** seperti `/user/{username}` → `:username` di Postman, isi via tab **Path Variables**.
- **Query params** ditandai `disabled: true` kecuali yang `required` — aktifkan kalau perlu.
- **Cookie auth** tidak perlu konfigurasi tambahan; Postman menanganinya otomatis setelah `POST /login`.
- **`POST /catalog/seed`** sengaja `include_in_schema=False` di FastAPI sehingga tidak muncul di collection — itu endpoint internal bootstrap, bukan public API.
