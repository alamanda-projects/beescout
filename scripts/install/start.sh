#!/usr/bin/env bash
# BeeScout — Start semua layanan
# Untuk first run dan pemakaian harian.

set -u
cd "$(dirname "$0")/../.." || exit 1

FIRST_RUN=false

if [ ! -f .env ]; then
  echo "ℹ File .env belum ada. Membuat konfigurasi lokal..."
  cp .env.example .env
  FIRST_RUN=true

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
    echo "✓ .env dibuat dan secret lokal di-generate."
  else
    echo "⚠ openssl tidak ditemukan. .env dibuat dari template; ganti nilai changeme_* sebelum production."
  fi
fi

if ! docker info >/dev/null 2>&1; then
  echo "✗ Docker belum jalan. Buka aplikasi Docker Desktop dulu."
  read -p "Tekan Enter untuk menutup..." _
  exit 1
fi

echo "── Menjalankan BeeScout ──────────────────────────────────────"
if [ "$FIRST_RUN" = true ]; then
  docker compose up --build -d
else
  docker compose up -d
fi
echo ""
docker compose ps
echo ""
echo "  Buka:"
echo "    User        → http://app.localhost"
echo "    Admin       → http://admin.localhost"
echo "    Setup Awal  → http://admin.localhost/setup"
echo ""

if [ -t 0 ] && [ -t 1 ]; then
  read -p "Tekan Enter untuk menutup..." _
fi
