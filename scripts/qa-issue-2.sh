#!/usr/bin/env bash
# Auto QA/QC untuk Issue #2 — Group Stakeholder Roles (Bisnis vs Teknis)
# https://github.com/alamanda-projects/beescout/issues/2
#
# Dijalankan dari root repo:
#   bash scripts/qa-issue-2.sh
#
# SDLC Tahap 4 (TEST) — verifikasi otomatis sebelum membuka PR.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=0
FAIL=0

check() {
  local label="$1"
  local cmd="$2"
  printf "  %-60s " "$label"
  if eval "$cmd" > /tmp/qa_out 2>&1; then
    echo "✓"
    PASS=$((PASS+1))
  else
    echo "✗"
    sed 's/^/      /' /tmp/qa_out | tail -5
    FAIL=$((FAIL+1))
  fi
}

ADMIN_TYPES="frontend-admin/src/types/contract.ts"
USER_TYPES="frontend-user/src/types/contract.ts"
ADMIN_NEW="frontend-admin/src/app/(protected)/contracts/new/page.tsx"
ADMIN_EDIT="frontend-admin/src/app/(protected)/contracts/[cn]/edit/page.tsx"
ADMIN_DETAIL="frontend-admin/src/app/(protected)/contracts/[cn]/page.tsx"
USER_NEW="frontend-user/src/app/(protected)/contracts/new/page.tsx"

echo "═══ AUTO QA — ISSUE #2 (Group Stakeholder Roles) ═══"
echo ""

echo "── 1. KONSTANTA & HELPER (types/contract.ts) ──"
check "STAKEHOLDER_ROLE_GROUPS export ada (admin)" \
  "grep -q 'export const STAKEHOLDER_ROLE_GROUPS' '$ADMIN_TYPES'"
check "STAKEHOLDER_ROLE_GROUPS export ada (user)" \
  "grep -q 'export const STAKEHOLDER_ROLE_GROUPS' '$USER_TYPES'"
check "STAKEHOLDER_ROLES (flat) backward-compat (admin)" \
  "grep -q 'export const STAKEHOLDER_ROLES' '$ADMIN_TYPES'"
check "STAKEHOLDER_ROLES (flat) backward-compat (user)" \
  "grep -q 'export const STAKEHOLDER_ROLES' '$USER_TYPES'"
check "getStakeholderRoleLabel helper (admin)" \
  "grep -q 'getStakeholderRoleLabel' '$ADMIN_TYPES'"
check "getStakeholderRoleLabel helper (user)" \
  "grep -q 'getStakeholderRoleLabel' '$USER_TYPES'"
check "Group 'Peran Bisnis' ada (admin)" \
  "grep -q 'Peran Bisnis' '$ADMIN_TYPES'"
check "Group 'Peran Teknis' ada (admin)" \
  "grep -q 'Peran Teknis' '$ADMIN_TYPES'"

echo ""
echo "── 2. INTEGRASI FORM (3 halaman) ──"
for f in "$ADMIN_NEW" "$ADMIN_EDIT" "$USER_NEW"; do
  short=$(echo "$f" | sed 's|frontend-||;s|/src/app/(protected)/contracts||')
  check "SelectGroup di-import di $short" \
    "grep -q 'SelectGroup' '$f'"
  check "SelectLabel di-import di $short" \
    "grep -q 'SelectLabel' '$f'"
  check "STAKEHOLDER_ROLE_GROUPS dipakai di $short" \
    "grep -q 'STAKEHOLDER_ROLE_GROUPS' '$f'"
done

echo ""
echo "── 3. DISPLAY DETAIL PAGE ──"
check "getStakeholderRoleLabel dipakai di [cn]/page.tsx" \
  "grep -q 'getStakeholderRoleLabel' '$ADMIN_DETAIL'"
check "Tidak ada lagi raw {s.role} di [cn]/page.tsx" \
  "! grep -qE '\\{s\\.role\\}' '$ADMIN_DETAIL'"

echo ""
echo "── 4. TYPESCRIPT TYPECHECK ──"
check "Typecheck frontend-admin lulus" \
  "( cd frontend-admin && npx tsc --noEmit )"
check "Typecheck frontend-user lulus" \
  "( cd frontend-user && npx tsc --noEmit )"

echo ""
echo "── 5. NEXT.JS BUILD VERIFICATION ──"
check "Production build frontend-admin sukses" \
  "( cd frontend-admin && npm run build > /tmp/build-admin.log 2>&1 )"

echo ""
echo "═══ RINGKASAN ═══"
echo "  ✓ PASS:  $PASS"
echo "  ✗ FAIL:  $FAIL"
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "  STATUS: ✅ QA LULUS — siap buka PR"
  exit 0
else
  echo "  STATUS: ❌ QA GAGAL — investigasi $FAIL kegagalan di atas"
  exit 1
fi
