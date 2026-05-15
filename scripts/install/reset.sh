#!/usr/bin/env bash
# BeeScout — Reset & Fresh Install
#
# Script ini menghapus SEMUA data BeeScout (database, images, .env) dan
# menjalankan ulang setup dari nol, seolah baru pertama kali install.
#
# ⚠️  PERINGATAN: Semua data kontrak, user, dan approval AKAN HILANG permanen.
#
# Jalankan dari root repo:
#   bash scripts/install/reset.sh
#
# Atau dari folder scripts/install/:
#   bash reset.sh

set -u

# Pindah ke root repo
cd "$(dirname "$0")/../.." || exit 1
REPO_ROOT="$(pwd)"

# Warna
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
  if [ -t 0 ] && [ -t 1 ]; then
    echo ""
    read -p "Tekan Enter untuk menutup..." _
  fi
}

trap pause_if_doubleclick EXIT

print_header "BeeScout — Reset & Fresh Install"
echo "  Folder repo: $REPO_ROOT"
echo ""
echo -e "  ${RED}⚠️  PERHATIAN${NC}"
echo "  Script ini akan menghapus:"
echo "    • Semua container BeeScout"
echo "    • Volume database (semua data kontrak & user hilang permanen)"
echo "    • Semua image Docker BeeScout"
echo "    • File .env (akan dibuat ulang dari template)"
echo ""

read -p "  Ketik 'RESET' untuk konfirmasi, atau tekan Enter untuk batal: " confirm
if [ "$confirm" != "RESET" ]; then
  echo ""
  print_warn "Dibatalkan. Tidak ada yang diubah."
  exit 0
fi

# ── Langkah 1: Cek Docker ──────────────────────────────────────────────────
print_header "Langkah 1/4 — Cek Docker"

if ! command -v docker >/dev/null 2>&1; then
  print_err "Docker belum terinstall."
  echo "  Install Docker Desktop dari: https://www.docker.com/products/docker-desktop/"
  exit 1
fi
print_ok "Docker terinstall"

if ! docker info >/dev/null 2>&1; then
  print_err "Docker belum jalan. Buka Docker Desktop lalu coba lagi."
  exit 1
fi
print_ok "Docker daemon berjalan"

# ── Langkah 2: Bersihkan semua resource BeeScout ───────────────────────────
print_header "Langkah 2/4 — Bersihkan Resource Docker"

echo "  Menghentikan dan menghapus container..."
docker compose down --remove-orphans 2>/dev/null || true
print_ok "Container dihentikan"

echo "  Menghapus volume database..."
docker volume rm beescout_beescout-data beescout_beescout-dev-data 2>/dev/null || true
print_ok "Volume database dihapus"

echo "  Menghapus image BeeScout..."
docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "^beescout|^alamandaprojects/beescout" | while read -r img; do
  docker rmi "$img" 2>/dev/null && echo "    - $img" || true
done
print_ok "Image dihapus"

echo "  Menghapus .env..."
rm -f .env
print_ok ".env dihapus"

# ── Langkah 3: Buat .env baru ──────────────────────────────────────────────
print_header "Langkah 3/4 — Buat Konfigurasi Baru"

cp .env.example .env
print_ok ".env dibuat dari .env.example"

if command -v openssl >/dev/null 2>&1; then
  TKN_KEY=$(openssl rand -hex 32)
  TKN_TOK=$(openssl rand -hex 32)
  SA_KEY=$(openssl rand -hex 32)
  SA_TOK=$(openssl rand -hex 32)
  MONGO_PASS=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)

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
  print_warn "COOKIE_SECURE diset ke 'false' untuk dev lokal (tanpa HTTPS)"
  echo ""
  echo -e "  Password MongoDB baru: ${YELLOW}$MONGO_PASS${NC}"
  echo "  (tersimpan di file .env)"
else
  print_warn "openssl tidak ditemukan — edit .env manual dan ganti semua nilai 'changeme_*'."
fi

# ── Langkah 4: Build & Start ───────────────────────────────────────────────
print_header "Langkah 4/4 — Build & Jalankan Ulang"
echo "  Proses ini membutuhkan waktu 5–15 menit (build dari awal)."
echo ""

if ! docker compose up --build -d; then
  print_err "Gagal start layanan. Cek pesan error di atas."
  exit 1
fi

print_ok "Semua layanan berjalan"
echo ""
docker compose ps

# ── Selesai ───────────────────────────────────────────────────────────────
print_header "Reset Selesai"
echo ""
echo -e "  Buka browser dan akses:"
echo -e "    ${GREEN}Aplikasi User  →${NC} http://app.localhost"
echo -e "    ${GREEN}Panel Admin    →${NC} http://admin.localhost"
echo ""
echo "  Database kosong. Buat akun Super Admin pertama lewat browser:"
echo ""
echo -e "    ${GREEN}Setup Awal     →${NC} http://admin.localhost/setup"
echo ""
echo "  Jika ingin database kontrak kosong, jangan centang opsi import contoh Data Contract."
echo ""
