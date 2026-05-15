#!/usr/bin/env bash
# BeeScout — Setup Wizard untuk Mac & Linux
#
# Untuk non-developer: klik dua kali file ini (atau jalankan di Terminal).
# Script ini akan:
#   1. Cek Docker terinstall & jalan
#   2. Buat .env dari template + generate secret otomatis
#   3. Jalankan semua layanan
#   4. Pandu Anda menambahkan entri /etc/hosts
#
# Aman dijalankan berulang kali — .env yang sudah ada tidak akan ditimpa.

set -u

# Pindah ke root repo (parent dari scripts/install/)
cd "$(dirname "$0")/../.." || exit 1
REPO_ROOT="$(pwd)"

# Warna untuk output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
  echo ""
  echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}  $1${NC}"
  echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
}

print_ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
print_warn() { echo -e "  ${YELLOW}!${NC} $1"; }
print_err()  { echo -e "  ${RED}✗${NC} $1"; }

pause_if_doubleclick() {
  # Jika dijalankan via double-click di Mac (.command), tahan terminal terbuka
  if [ -t 0 ] && [ -t 1 ]; then
    echo ""
    read -p "Tekan Enter untuk menutup..." _
  fi
}

trap pause_if_doubleclick EXIT

print_header "BeeScout Setup Wizard"
echo "  Folder repo: $REPO_ROOT"

# ── Langkah 1: Cek Docker ──────────────────────────────────────────────────────
print_header "Langkah 1/4 — Cek Docker"

if ! command -v docker >/dev/null 2>&1; then
  print_err "Docker belum terinstall."
  echo ""
  echo "  Silakan install Docker Desktop terlebih dahulu:"
  echo "    https://www.docker.com/products/docker-desktop/"
  echo ""
  echo "  Setelah install, buka aplikasi Docker Desktop, tunggu sampai ikon"
  echo "  whale di status bar tidak berkedip, lalu jalankan script ini lagi."
  exit 1
fi
print_ok "Docker terinstall ($(docker --version | head -1))"

if ! docker info >/dev/null 2>&1; then
  print_err "Docker belum jalan."
  echo ""
  echo "  Buka aplikasi Docker Desktop, tunggu sampai status hijau,"
  echo "  lalu jalankan script ini lagi."
  exit 1
fi
print_ok "Docker daemon berjalan"

if ! docker compose version >/dev/null 2>&1; then
  print_err "Docker Compose v2 tidak ditemukan."
  echo "  Update Docker Desktop ke versi terbaru."
  exit 1
fi
print_ok "Docker Compose v2 tersedia"

# ── Langkah 2: Setup .env ──────────────────────────────────────────────────────
print_header "Langkah 2/4 — Konfigurasi .env"

if [ -f .env ]; then
  print_warn ".env sudah ada — dilewati (tidak ditimpa)."
else
  cp .env.example .env
  print_ok ".env dibuat dari .env.example"

  # Generate secrets otomatis pakai openssl
  if command -v openssl >/dev/null 2>&1; then
    TKN_KEY=$(openssl rand -hex 32)
    TKN_TOK=$(openssl rand -hex 32)
    SA_KEY=$(openssl rand -hex 32)
    SA_TOK=$(openssl rand -hex 32)
    MONGO_PASS=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)

    # Mac sed butuh '' setelah -i; Linux tidak. Pakai fallback portable.
    sed_inplace() {
      if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$1" .env
      else
        sed -i "$1" .env
      fi
    }

    sed_inplace "s|MONGODB_PASS=changeme_strong_password_here|MONGODB_PASS=$MONGO_PASS|"
    sed_inplace "s|TKN_SECRET_KEY=changeme_generate_with_openssl_rand_hex_32|TKN_SECRET_KEY=$TKN_KEY|"
    sed_inplace "s|TKN_SECRET_TOKEN=changeme_generate_with_openssl_rand_hex_32|TKN_SECRET_TOKEN=$TKN_TOK|"
    sed_inplace "s|SA_SECRET_KEY=changeme_generate_with_openssl_rand_hex_32|SA_SECRET_KEY=$SA_KEY|"
    sed_inplace "s|SA_SECRET_TOKEN=changeme_generate_with_openssl_rand_hex_32|SA_SECRET_TOKEN=$SA_TOK|"
    sed_inplace "s|COOKIE_SECURE=true|COOKIE_SECURE=false|"

    print_ok "Secret JWT & password MongoDB di-generate otomatis"
    print_warn "COOKIE_SECURE diset ke 'false' karena dev lokal (tanpa HTTPS)"
    echo ""
    echo "  Password MongoDB Anda: ${YELLOW}$MONGO_PASS${NC}"
    echo "  (catat jika perlu — tersimpan juga di file .env)"
  else
    print_warn "openssl tidak ditemukan — Anda perlu edit .env manual."
    echo "  Buka file .env dan ganti semua nilai 'changeme_*' dengan password kuat."
  fi
fi

# ── Langkah 3: Build & Start ──────────────────────────────────────────────────
print_header "Langkah 3/4 — Build & Jalankan Layanan"
echo "  Proses ini bisa makan waktu 5-15 menit di first run (download image)."
echo "  Selanjutnya jauh lebih cepat."
echo ""

if ! docker compose up --build -d; then
  print_err "Gagal start layanan. Cek pesan error di atas."
  exit 1
fi

print_ok "Semua layanan berjalan"
echo ""
docker compose ps

# ── Langkah 4: /etc/hosts ─────────────────────────────────────────────────────
print_header "Langkah 4/4 — Konfigurasi /etc/hosts"

NEED_HOSTS=false
if ! grep -q "app.localhost" /etc/hosts 2>/dev/null; then NEED_HOSTS=true; fi
if ! grep -q "admin.localhost" /etc/hosts 2>/dev/null; then NEED_HOSTS=true; fi

if [ "$NEED_HOSTS" = true ]; then
  print_warn "File /etc/hosts perlu diupdate (butuh password admin)."
  echo ""
  echo "  Saya akan menambahkan 2 baris berikut ke /etc/hosts:"
  echo "    127.0.0.1   app.localhost"
  echo "    127.0.0.1   admin.localhost"
  echo ""
  read -p "  Lanjutkan? Tekan [y] lalu Enter (atau lewati dengan [n]): " ans
  if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
    echo ""
    echo "  Masukkan password Mac/Linux Anda saat diminta:"
    {
      echo "127.0.0.1   app.localhost"
      echo "127.0.0.1   admin.localhost"
    } | sudo tee -a /etc/hosts >/dev/null
    print_ok "/etc/hosts berhasil diupdate"
  else
    print_warn "Dilewati. Tambah manual nanti:"
    echo "    sudo nano /etc/hosts"
    echo "    Tambah:"
    echo "      127.0.0.1   app.localhost"
    echo "      127.0.0.1   admin.localhost"
  fi
else
  print_ok "/etc/hosts sudah berisi entri yang dibutuhkan"
fi

# ── Selesai ───────────────────────────────────────────────────────────────────
print_header "Selesai! 🎉"
echo ""
echo -e "  Buka browser dan akses:"
echo -e "    ${GREEN}Aplikasi User  →${NC} http://app.localhost"
echo -e "    ${GREEN}Panel Admin    →${NC} http://admin.localhost"
echo ""
echo "  Akun belum ada — lihat 'Langkah 4' di docs/quick-start-non-tech.md"
echo "  untuk cara membuat akun Super Admin pertama."
echo ""
echo "  Perintah berikutnya:"
echo "    scripts/install/start.sh   → start lagi setelah komputer restart"
echo "    scripts/install/stop.sh    → matikan semua layanan"
echo ""
