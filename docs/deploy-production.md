# Self-Hosting BeeScout di Production — Runbook & Checklist

> BeeScout adalah proyek **open-source**. Siapa pun boleh meng-clone repo ini
> dan men-deploy instance-nya **sendiri**. Dokumen ini panduan untuk **operator**
> mana pun yang melakukannya — bukan untuk satu instance kanonik tertentu.
>
> "Operator" = orang/tim yang men-deploy & mengelola instance. Setiap deployment
> berdiri sendiri: domain sendiri, secret sendiri, akun root sendiri.
>
> Jangan umumkan instance ke publik sebelum seluruh [Checklist Go-Live](#checklist-go-live)
> ter-tick (atau dijustifikasi mengapa tidak applicable untuk lingkungan Anda).
>
> Untuk setup development lokal lihat [getting-started.md](../getting-started.md).
> Untuk rotasi & penyimpanan secret lihat [credentials.md](credentials.md).

---

## Ringkasan arsitektur saat deploy

```
            ┌─────────────────────── TLS terminator ───────────────────────┐
internet ──▶│  Caddy / Cloudflare / reverse proxy eksternal  (HTTPS :443)   │
            └───────────────────────────────┬───────────────────────────────┘
                                            │ HTTP :80 (jaringan privat)
                                  ┌─────────▼─────────┐
                                  │  nginx (gateway)  │  default.conf.template
                                  └────┬─────────┬────┘
                       app.example.com │         │ admin.example.com
                          ┌────────────▼──┐   ┌──▼─────────────┐
                          │ frontend-user │   │ frontend-admin │
                          └───────┬───────┘   └───────┬────────┘
                                  └──── /api/ ────────┘
                                        │
                                  ┌─────▼─────┐     ┌──────────┐
                                  │  backend  │────▶│ MongoDB  │ (internal-net)
                                  └───────────┘     └──────────┘
```

nginx di repo ini **hanya melayani HTTP :80**. TLS diterminasi di lapisan
depan — lihat [TLS / HTTPS](#2-tls--https-wajib).

---

## 1. Domain & Routing

1. Tentukan dua subdomain — satu untuk user, satu untuk admin. Pisahkan host;
   jangan satu domain. Contoh: `app.example.com` + `admin.example.com`.
2. Set di `.env` production:
   ```dotenv
   BEESCOUT_USER_DOMAIN=app.example.com
   BEESCOUT_ADMIN_DOMAIN=admin.example.com
   ```
3. Buat DNS A/AAAA record kedua subdomain → IP server.
4. nginx me-resolve subdomain via `envsubst` saat container start. Permintaan
   dengan Host yang tidak cocok ditolak `444` oleh default-server block.
5. **Batasi akses admin panel.** `default.conf.template` punya blok IP allowlist
   (komentar) di server admin — aktifkan dengan CIDR kantor/VPN:
   ```nginx
   allow 203.0.113.10;   # IP kantor
   allow 10.0.0.0/8;     # subnet VPN
   deny  all;
   ```

## 2. TLS / HTTPS (WAJIB)

nginx repo ini tidak meng-handle TLS. Pilih salah satu:

**Opsi A — Cloudflare (paling sederhana).** Proxy domain lewat Cloudflare,
set SSL mode "Full (strict)". Cloudflare menangani cert + redirect + HSTS.

**Opsi B — Caddy sebagai TLS terminator** di depan nginx:
```
app.example.com, admin.example.com {
    reverse_proxy nginx:80
}
```
Caddy otomatis mengambil cert Let's Encrypt & redirect HTTP→HTTPS.

**Opsi C — certbot + nginx 443 block.** Tambah server block `listen 443 ssl`
ke `default.conf.template` dengan path cert, dan ubah server `:80` jadi
`return 301 https://$host$request_uri;`. Hanya tempuh ini bila tidak ada
proxy eksternal.

Apa pun opsinya, pastikan:
- HTTP → HTTPS redirect aktif (301).
- Header HSTS terkirim — `default.conf.template` sudah mengirim
  `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  (browser hanya menghormatinya di atas HTTPS).
- `COOKIE_SECURE=true` di `.env` (default sudah `true`).
- Cek grade di [SSL Labs](https://www.ssllabs.com/ssltest/) — target ≥ A.

## 3. Secrets — generasi & rotasi

Generate tiap secret unik:
```bash
openssl rand -hex 32   # jalankan terpisah untuk tiap key di bawah
```

| Variabel `.env`   | Cara isi                                  |
|-------------------|--------------------------------------------|
| `MONGODB_PASS`    | Password kuat unik, min 24 char, non-kamus |
| `TKN_SECRET_KEY`  | `openssl rand -hex 32`                     |
| `TKN_SECRET_TOKEN`| `openssl rand -hex 32` (nilai berbeda)     |
| `SA_SECRET_KEY`   | `openssl rand -hex 32`                     |
| `SA_SECRET_TOKEN` | `openssl rand -hex 32` (nilai berbeda)     |

Verifikasi tidak ada placeholder tersisa:
```bash
grep -i changeme .env          # harus kosong
git ls-files | grep -E '^\.env$'   # harus kosong — .env tidak boleh ter-commit
```

Simpan semua secret di password manager / vault. Prosedur rotasi:
lihat [credentials.md → Rotasi Secret](credentials.md#rotasi-secret-production).

## 4. CORS & Cookie

- `ALLOWED_ORIGINS` — hanya domain production HTTPS, dipisah koma. Tidak boleh
  `*`, tidak boleh skema `http://`.
  ```dotenv
  ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
  ```
- `COOKIE_SECURE=true`.
- Cookie sudah di-set `httponly=true` + `samesite=Strict` oleh backend
  (hardcoded di `main.py` — tidak perlu env). Verifikasi di browser devtools:
  cookie auth bertanda `HttpOnly` + `Secure`.

## 5. Rate limiting & DoS

- `BEESCOUT_RATE_LOGIN` (default `10`/menit) — turunkan ke `5` jika perlu.
- `BEESCOUT_RATE_API` (default `30`/detik).
- nginx menolak request tanpa Host valid (`444`) — sudah default via
  default-server block.
- Pertimbangkan WAF eksternal (Cloudflare / fail2ban) sebagai lapisan tambahan.

## 6. Bootstrap akun pertama

1. Setelah deploy, buka `https://admin.example.com/setup` → buat akun root pertama.
2. Verifikasi `POST /setup` mengembalikan `409` setelah root ada (self-disabling):
   ```bash
   curl -s https://admin.example.com/api/setup/status   # {"setup_complete": true}
   ```
3. Simpan password root di vault — **jangan** kirim via email/chat.
4. (Opsional) bila #32 sudah selesai, root bisa di-seed via `SEED_ROOT_*` env.

## 7. MongoDB hardening

- Port `27017` **tidak** di-expose ke host. `docker-compose.yml` (production)
  service `db` tidak punya blok `ports:` — verifikasi tetap demikian.
  (Override dev `docker-compose.dev.yml` sengaja meng-expose untuk tooling —
  jangan pakai file itu di production.)
- Jadwalkan backup otomatis:
  ```bash
  # contoh cron harian — simpan dump ke luar server
  docker exec beescout-db-1 mongodump --archive --gzip \
    --uri "mongodb://$MONGODB_USER:$MONGODB_PASS@localhost:27017/$MONGODB_DB?authSource=admin" \
    > backup-$(date +%F).archive.gz
  ```
- **Uji restore minimal 1×** sebelum go-live (`mongorestore --archive --gzip`).
- Cek log startup backend — tidak boleh ada `DuplicateKeyError` saat build
  unique index (lihat troubleshooting di [CLAUDE.md](../CLAUDE.md)).

## 8. Logging & observability

- Backend log level production: `INFO` (bukan `DEBUG`).
- Rotasi log — **sudah dikonfigurasi** di `docker-compose.yml` lewat anchor
  `x-logging` (`json-file`, `max-size: 10m`, `max-file: 3`) pada semua service.
  Tidak perlu setup manual; cegah disk bloat (#20).
- Healthcheck: `GET /health` → `{"status":"ok","version":"..."}` (sudah ada).
- Pasang monitoring uptime (UptimeRobot / Healthchecks.io) yang men-poll
  `/health`, alert ke email operator instance.

## 9. Audit codebase sebelum go-live

```bash
make test                            # backend pytest + 2 typecheck — semua hijau
for s in scripts/qa-*.sh; do bash "$s"; done   # tiap script exit 0
bash scripts/qa-prod-readiness.sh    # cek statis checklist go-live (lihat catatan)
```

> `qa-prod-readiness.sh` mengotomasi item checklist yang bisa diverifikasi
> statis: `.env` tidak ter-commit, MongoDB tidak di-expose, rotasi log aktif,
> dan — bila dijalankan di server yang punya `.env` — tidak ada placeholder
> `changeme`, `COOKIE_SECURE` bukan `false`, `ALLOWED_ORIGINS` tanpa wildcard /
> `http://`. Jalankan **di server production** agar check `.env` ikut tereksekusi.

- Jalankan skill `/security-review` pada branch yang akan di-deploy.
- Pastikan tidak ada `console.log` / `print()` yang membocorkan data sensitif.
- Pastikan tidak ada credential hardcoded di source.
- Selesaikan bug critical yang masih open sebelum go-live.

## 10. Dokumentasi operasional

- [credentials.md](credentials.md) — prosedur rotasi secret (lihat bagian
  [Rotasi Secret](credentials.md#rotasi-secret-production)).
- Dokumen ini — runbook deploy.
- Incident response — lihat [bagian di bawah](#incident-response).
- [SECURITY.md](../SECURITY.md) — kanal pelaporan kerentanan; verifikasi masih valid.

---

## Prosedur deploy

```bash
# 1. Di server, clone repo & siapkan .env
git clone <repo> && cd beescout
cp .env.example .env
# edit .env: domain, secrets (bagian 3), ALLOWED_ORIGINS, COOKIE_SECURE=true

# 2. Build & start seluruh stack
make up                          # docker compose up --build -d

# 3. Verifikasi
docker compose ps                # semua service Up
curl -s https://admin.example.com/api/health   # {"status":"ok"}

# 4. Bootstrap akun root — buka /setup di browser (bagian 6)
```

### Rollback

```bash
git checkout <tag-atau-commit-stabil-sebelumnya>
make up                          # rebuild dari kode lama
# bila perubahan schema: restore dump MongoDB pra-deploy (bagian 7)
```

---

## Incident Response

| Situasi | Langkah |
|---|---|
| Suspect breach / akun bocor | Rotasi semua secret (bagian 3) → `make up` → revoke sesi (restart backend meng-invalidasi token via secret baru) |
| Data corrupt / loss | Restore dump MongoDB terbaru (bagian 7) |
| Service down | `docker compose ps` & `docker compose logs -f <service>`; cek disk (`docker system df`) |
| MongoDB crash-loop | Lihat troubleshooting WiredTiger / DuplicateKeyError di [CLAUDE.md](../CLAUDE.md) |

- **Kontak operasional:** operator/admin instance Anda sendiri — tentukan &
  catat di runbook internal organisasi Anda (BeeScout tidak menyediakan
  dukungan operasional untuk instance self-hosted).
- **Lokasi log:** `docker compose logs` (driver json-file, ter-rotate).
- **Kerentanan pada software BeeScout** (bukan masalah operasional instance
  Anda): laporkan ke proyek lewat [SECURITY.md](../SECURITY.md).

---

## Checklist Go-Live

Checklist ini untuk **operator** yang men-deploy instance BeeScout sendiri.
Salin ke catatan rilis internal Anda dan tick satu per satu. Item yang tidak
applicable untuk lingkungan Anda wajib diberi justifikasi tertulis.

### Domain & TLS
- [ ] Domain user & admin dibeli, DNS A/AAAA mengarah ke server
- [ ] `BEESCOUT_USER_DOMAIN` & `BEESCOUT_ADMIN_DOMAIN` di-set di `.env`
- [ ] TLS aktif, HTTP→HTTPS redirect 301, SSL Labs grade ≥ A
- [ ] Admin panel dibatasi IP allowlist (nginx) atau kanal privat

### Secrets
- [ ] `MONGODB_PASS` diganti — password kuat unik
- [ ] `TKN_SECRET_KEY` / `TKN_SECRET_TOKEN` di-generate (`openssl rand -hex 32`)
- [ ] `SA_SECRET_KEY` / `SA_SECRET_TOKEN` di-generate
- [ ] `grep -i changeme .env` kosong
- [ ] `.env` tidak ter-commit; semua secret tersimpan di vault

### Keamanan aplikasi
- [ ] `ALLOWED_ORIGINS` hanya domain HTTPS production
- [ ] `COOKIE_SECURE=true`; cookie `HttpOnly`+`Secure` terverifikasi di devtools
- [ ] Rate limit login & API di-review
- [ ] MongoDB tidak meng-expose port `27017` ke host

### Operasional
- [ ] Akun root pertama dibuat via `/setup`; `/setup` mengembalikan `409` setelahnya
- [ ] Backup MongoDB terjadwal; prosedur restore diuji ≥ 1×
- [ ] Rotasi log aktif; monitoring uptime + alert email terpasang
- [ ] `make test` hijau; semua `scripts/qa-*.sh` exit 0
- [ ] `bash scripts/qa-prod-readiness.sh` exit 0 (dijalankan di server, `.env` ada)
- [ ] `/security-review` dijalankan pada branch deploy

### Verifikasi akhir
- [ ] Kedua subdomain Anda (`https://app...` & `https://admin...`) — HTTPS, login normal
- [ ] Operator memverifikasi langsung di server production
