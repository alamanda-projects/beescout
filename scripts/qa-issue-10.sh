#!/usr/bin/env bash
# QA — Issue #10: Enter key auto-submit + duplikat kontrak
#
# Verifikasi semua fix untuk bug #10 (sub-issues #11, #12, #13) sudah ada
# dan TypeScript compile bersih.
#
# Jalankan dari root repo:
#   bash scripts/qa-issue-10.sh
#
# Exit 0 jika semua pass, 1 jika ada yang gagal.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0
echo "── QA: issue #10 — Enter key auto-submit + duplikat kontrak ──────"

check() {
  local desc="$1"; local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "✓ $desc"
  else
    echo "✗ $desc"
    FAIL=$((FAIL+1))
  fi
}

# ── Bug A: Enter key guard ────────────────────────────────────────────────────
check "admin new/page.tsx: onKeyDown Enter guard ada" \
  "grep -q \"e.key === 'Enter'\" 'frontend-admin/src/app/(protected)/contracts/new/page.tsx'"

check "admin new/page.tsx: TEXTAREA exclusion ada" \
  "grep -q \"tagName !== 'TEXTAREA'\" 'frontend-admin/src/app/(protected)/contracts/new/page.tsx'"

check "admin edit/page.tsx: onKeyDown Enter guard ada" \
  "grep -q \"e.key === 'Enter'\" 'frontend-admin/src/app/(protected)/contracts/[cn]/edit/page.tsx'"

check "admin edit/page.tsx: TEXTAREA exclusion ada" \
  "grep -q \"tagName !== 'TEXTAREA'\" 'frontend-admin/src/app/(protected)/contracts/[cn]/edit/page.tsx'"

check "user new/page.tsx: onKeyDown Enter guard ada" \
  "grep -q \"e.key === 'Enter'\" 'frontend-user/src/app/(protected)/contracts/new/page.tsx'"

check "user new/page.tsx: TEXTAREA exclusion ada" \
  "grep -q \"tagName !== 'TEXTAREA'\" 'frontend-user/src/app/(protected)/contracts/new/page.tsx'"

# ── Bug B: Duplikat kontrak ───────────────────────────────────────────────────
check "backend: unique index pada contract_number ada (ensure_indexes)" \
  "grep -q 'create_index.*contract_number.*unique' repository/app/main.py"

check "backend: DuplicateKeyError import ada" \
  "grep -q 'from pymongo.errors import DuplicateKeyError' repository/app/main.py"

check "backend: 409 response saat DuplicateKeyError ada" \
  "grep -A5 'except DuplicateKeyError' repository/app/main.py | grep -q '409'"

check "dedupe_contracts.py script ada (untuk cleanup data lama)" \
  "test -f repository/scripts/dedupe_contracts.py"

# ── Post-save redirect & feedback ────────────────────────────────────────────
check "admin new/page.tsx: toast.success setelah simpan ada" \
  "grep -q \"toast.success\" 'frontend-admin/src/app/(protected)/contracts/new/page.tsx'"

check "admin new/page.tsx: router.push ke detail kontrak ada" \
  "grep -q \"router.push\" 'frontend-admin/src/app/(protected)/contracts/new/page.tsx'"

check "user new/page.tsx: toast.success setelah simpan ada" \
  "grep -q \"toast.success\" 'frontend-user/src/app/(protected)/contracts/new/page.tsx'"

check "user new/page.tsx: router.push ke detail kontrak ada" \
  "grep -q \"router.push\" 'frontend-user/src/app/(protected)/contracts/new/page.tsx'"

# ── TypeScript compile ────────────────────────────────────────────────────────
echo ""
echo "── TypeScript compile ──────────────────────────────────────────"
if cd frontend-admin && npx tsc --noEmit 2>&1; then
  echo "✓ frontend-admin TypeScript OK"
  cd "$ROOT"
else
  echo "✗ frontend-admin TypeScript GAGAL"
  FAIL=$((FAIL+1))
  cd "$ROOT"
fi

if cd frontend-user && npx tsc --noEmit 2>&1; then
  echo "✓ frontend-user TypeScript OK"
  cd "$ROOT"
else
  echo "✗ frontend-user TypeScript GAGAL"
  FAIL=$((FAIL+1))
  cd "$ROOT"
fi

echo "────────────────────────────────────────────────────────────────"
if [ "$FAIL" -gt 0 ]; then
  echo "GAGAL ($FAIL check)."
  exit 1
fi
echo "OK — semua check lulus."
exit 0
