#!/usr/bin/env bash
# BeeScout — Start semua layanan
# Untuk pemakaian harian setelah setup pertama selesai.

set -u
cd "$(dirname "$0")/../.." || exit 1

if [ ! -f .env ]; then
  echo "✗ File .env belum ada. Jalankan dulu: scripts/install/setup.sh"
  read -p "Tekan Enter untuk menutup..." _
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "✗ Docker belum jalan. Buka aplikasi Docker Desktop dulu."
  read -p "Tekan Enter untuk menutup..." _
  exit 1
fi

echo "── Menjalankan BeeScout ──────────────────────────────────────"
docker compose up -d
echo ""
docker compose ps
echo ""
echo "  Buka:"
echo "    User  → http://app.localhost"
echo "    Admin → http://admin.localhost"
echo ""

if [ -t 0 ] && [ -t 1 ]; then
  read -p "Tekan Enter untuk menutup..." _
fi
