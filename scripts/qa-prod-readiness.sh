#!/usr/bin/env bash
# QA — Production readiness check (Issue #36)
#
# Mengotomasi item checklist go-live yang bisa diverifikasi secara statis,
# tanpa akses ke server. Bukan pengganti verifikasi operator langsung —
# lihat docs/deploy-production.md untuk checklist lengkap.
#
# Yang DICEK selalu (aman di CI, tidak butuh .env):
#   (1) .env tidak ter-commit ke git
#   (2) docker-compose.yml production tidak meng-expose port MongoDB ke host
#   (3) docker-compose.yml punya rotasi log (cegah disk bloat — #20)
#
# Yang DICEK hanya bila .env ada (lewati dengan SKIP bila tidak ada):
#   (4) Tidak ada placeholder `changeme` tersisa di .env
#   (5) COOKIE_SECURE tidak di-set `false`
#   (6) ALLOWED_ORIGINS tidak mengandung `*` atau skema `http://`
#
# Jalankan dari root repo:
#   bash scripts/qa-prod-readiness.sh
#
# Exit 0 jika bersih, 1 jika ada pelanggaran.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0
COMPOSE="docker-compose.yml"

echo "── QA: production readiness ────────────────────────────────────"

# ─── Check 1: .env tidak ter-commit ───────────────────────────────────
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo "✗ .env ter-track oleh git — secret production bisa bocor."
  echo "  Jalankan: git rm --cached .env  (dan pastikan ada di .gitignore)"
  FAIL=$((FAIL+1))
else
  echo "✓ .env tidak ter-commit ke git"
fi

# ─── Check 2: MongoDB tidak di-expose ke host (production compose) ────
if [ ! -f "$COMPOSE" ]; then
  echo "✗ $COMPOSE tidak ditemukan"
  FAIL=$((FAIL+1))
elif grep -qE '^\s*-\s*"?27017:27017"?' "$COMPOSE"; then
  echo "✗ $COMPOSE meng-expose port 27017 ke host — MongoDB harus internal."
  echo "  Hapus blok ports: pada service db (override dev boleh tetap punya)."
  FAIL=$((FAIL+1))
else
  echo "✓ MongoDB tidak di-expose ke host di $COMPOSE"
fi

# ─── Check 3: Rotasi log dikonfigurasi ────────────────────────────────
if [ -f "$COMPOSE" ] && grep -qE 'max-size' "$COMPOSE"; then
  echo "✓ Rotasi log Docker dikonfigurasi di $COMPOSE"
else
  echo "✗ $COMPOSE tidak punya rotasi log (max-size) — risiko disk bloat."
  echo "  Tambahkan logging: driver json-file dengan max-size/max-file."
  FAIL=$((FAIL+1))
fi

# ─── Check 4-6: hanya bila .env ada ───────────────────────────────────
if [ ! -f .env ]; then
  echo "• .env tidak ada — lewati check secret/CORS (jalankan lagi di server)."
else
  # 4 — placeholder changeme
  if grep -iq 'changeme' .env; then
    echo "✗ .env masih mengandung placeholder 'changeme' — secret belum diisi."
    FAIL=$((FAIL+1))
  else
    echo "✓ Tidak ada placeholder 'changeme' di .env"
  fi

  # 5 — COOKIE_SECURE tidak false
  cookie_secure=$(grep -E '^COOKIE_SECURE=' .env | tail -1 | cut -d= -f2- | tr -d '"' | tr -d ' ' | tr '[:upper:]' '[:lower:]')
  if [ "$cookie_secure" = "false" ]; then
    echo "✗ COOKIE_SECURE=false — wajib true di production (HTTPS)."
    FAIL=$((FAIL+1))
  else
    echo "✓ COOKIE_SECURE tidak di-set false"
  fi

  # 6 — ALLOWED_ORIGINS tanpa wildcard / http://
  origins=$(grep -E '^ALLOWED_ORIGINS=' .env | tail -1 | cut -d= -f2- | tr -d '"')
  if echo "$origins" | grep -q '\*'; then
    echo "✗ ALLOWED_ORIGINS mengandung '*' — terlalu permisif untuk production."
    FAIL=$((FAIL+1))
  elif echo "$origins" | grep -qE 'http://'; then
    echo "✗ ALLOWED_ORIGINS mengandung skema http:// — production harus HTTPS."
    FAIL=$((FAIL+1))
  else
    echo "✓ ALLOWED_ORIGINS hanya origin HTTPS spesifik"
  fi
fi

echo "────────────────────────────────────────────────────────────────"

if [ "$FAIL" -gt 0 ]; then
  echo "GAGAL ($FAIL check). Lihat docs/deploy-production.md."
  exit 1
fi

echo "OK — semua check production-readiness lulus."
exit 0
