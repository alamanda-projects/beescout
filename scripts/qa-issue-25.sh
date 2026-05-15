#!/usr/bin/env bash
# QA — Issue #25: UX parity user panel ↔ admin panel
#
# Verifikasi semua gap (G1–G11) dari issue #25 + #19 sudah diperbaiki.
#
# Jalankan dari root repo:
#   bash scripts/qa-issue-25.sh
#
# Exit 0 jika semua pass, 1 jika ada yang gagal.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0
echo "── QA: issue #25 — UX parity user panel ↔ admin panel ──────────"

check() {
  local desc="$1"; local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "✓ $desc"
  else
    echo "✗ $desc"
    FAIL=$((FAIL+1))
  fi
}

# ── G1: Stakeholder role label ────────────────────────────────────────────────
check "G1: getStakeholderRoleLabel dipakai di user [cn]/page.tsx" \
  "grep -q 'getStakeholderRoleLabel' 'frontend-user/src/app/(protected)/contracts/[cn]/page.tsx'"

# ── G2: Tab JSON Raw ──────────────────────────────────────────────────────────
check "G2: Tab JSON Raw ada di user [cn]/page.tsx" \
  "grep -q 'value=\"raw\"' 'frontend-user/src/app/(protected)/contracts/[cn]/page.tsx'"

# ── G3: standard_version InfoRow ─────────────────────────────────────────────
check "G3: standard_version InfoRow ada di user [cn]/page.tsx" \
  "grep -q 'standard_version' 'frontend-user/src/app/(protected)/contracts/[cn]/page.tsx'"

# ── G4: Edit button + ImportYamlButton ───────────────────────────────────────
check "G4: Edit button ada di user [cn]/page.tsx" \
  "grep -q 'contracts/\${cn}/edit' 'frontend-user/src/app/(protected)/contracts/[cn]/page.tsx'"

check "G4: ImportYamlButton ada di user [cn]/page.tsx" \
  "grep -q 'ImportYamlButton' 'frontend-user/src/app/(protected)/contracts/[cn]/page.tsx'"

# ── G5: QualityRulesEditor mode switch ───────────────────────────────────────
check "G5: canSwitchMode={true} ada di user new/page.tsx" \
  "grep -q 'canSwitchMode={true}' 'frontend-user/src/app/(protected)/contracts/new/page.tsx'"

check "G5: userMode dinamis (bukan hardcoded biz) di user new/page.tsx" \
  "grep -q \"userMode={userRole\" 'frontend-user/src/app/(protected)/contracts/new/page.tsx'"

# ── G6+G7: field-help.ts + Tooltips ──────────────────────────────────────────
check "G7: field-help.ts ada di frontend-user/src/lib/" \
  "test -f 'frontend-user/src/lib/field-help.ts'"

check "G6: DATA_TYPE_HELP dipakai di user new/page.tsx" \
  "grep -q 'DATA_TYPE_HELP' 'frontend-user/src/app/(protected)/contracts/new/page.tsx'"

check "G6: COLUMN_FLAG_HELP dipakai di user new/page.tsx" \
  "grep -q 'COLUMN_FLAG_HELP' 'frontend-user/src/app/(protected)/contracts/new/page.tsx'"

check "G6: tooltip.tsx component ada di frontend-user/src/components/ui/" \
  "test -f 'frontend-user/src/components/ui/tooltip.tsx'"

# ── G8+G9: Constants tidak inline, ada di types ───────────────────────────────
check "G8: CONSUMPTION_MODES tidak lagi inline di user new/page.tsx" \
  "! grep -q \"CONSUMPTION_MODES = \\[\" 'frontend-user/src/app/(protected)/contracts/new/page.tsx'"

check "G9: CONTRACT_TYPES export ada di user types/contract.ts" \
  "grep -q 'export const CONTRACT_TYPES' 'frontend-user/src/types/contract.ts'"

check "G9: CONSUMPTION_MODES export ada di user types/contract.ts" \
  "grep -q 'export const CONSUMPTION_MODES' 'frontend-user/src/types/contract.ts'"

check "G9: RETENTION_UNITS export ada di user types/contract.ts" \
  "grep -q 'export const RETENTION_UNITS' 'frontend-user/src/types/contract.ts'"

check "G9: QUALITY_DIMENSIONS export ada di user types/contract.ts" \
  "grep -q 'export const QUALITY_DIMENSIONS' 'frontend-user/src/types/contract.ts'"

# ── G10+G11: Edit page + Ports ────────────────────────────────────────────────
check "G10: User edit page ada di frontend-user/src/app/(protected)/contracts/[cn]/edit/page.tsx" \
  "test -f 'frontend-user/src/app/(protected)/contracts/[cn]/edit/page.tsx'"

check "G10: User edit page menggunakan updateContract dari @/lib/api/contracts" \
  "grep -q 'updateContract' 'frontend-user/src/app/(protected)/contracts/[cn]/edit/page.tsx'"

check "G10: Success message approval ada di user edit page" \
  "grep -q 'menunggu persetujuan' 'frontend-user/src/app/(protected)/contracts/[cn]/edit/page.tsx'"

check "G11: Ports section (addPort) ada di user edit page" \
  "grep -q 'addPort' 'frontend-user/src/app/(protected)/contracts/[cn]/edit/page.tsx'"

check "G5: canSwitchMode={true} ada di user edit page" \
  "grep -q 'canSwitchMode={true}' 'frontend-user/src/app/(protected)/contracts/[cn]/edit/page.tsx'"

# ── TypeScript compile ────────────────────────────────────────────────────────
echo ""
echo "── TypeScript compile ──────────────────────────────────────────"
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
