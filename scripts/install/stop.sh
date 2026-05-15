#!/usr/bin/env bash
# BeeScout — Stop semua layanan (data tidak terhapus)

set -u
cd "$(dirname "$0")/../.." || exit 1

echo "── Menghentikan BeeScout ─────────────────────────────────────"
docker compose down
echo ""
echo "  Selesai. Data MongoDB tetap aman di volume Docker."
echo "  Untuk start lagi: scripts/install/start.sh"
echo ""

if [ -t 0 ] && [ -t 1 ]; then
  read -p "Tekan Enter untuk menutup..." _
fi
