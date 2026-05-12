#!/usr/bin/env bash
# Auto QA/QC untuk Issue #1 — Tooltip bilingual untuk checkbox & label teknis
# https://github.com/alamanda-projects/beescout/issues/1
#
# Dijalankan dari root repo:
#   bash scripts/qa-issue-1.sh
#
# Skrip ini adalah contoh penerapan SDLC Tahap 4 (TEST) — verifikasi otomatis
# yang dijalankan sebelum membuka PR. Setiap PR yang menyentuh form Data
# Contract sebaiknya menyertakan skrip QA serupa.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=0
FAIL=0
WARN=0

check() {
  local label="$1"
  local cmd="$2"
  printf "  %-55s " "$label"
  if eval "$cmd" > /tmp/qa_out 2>&1; then
    echo "✓"
    PASS=$((PASS+1))
  else
    echo "✗"
    sed 's/^/      /' /tmp/qa_out | tail -5
    FAIL=$((FAIL+1))
  fi
}

warn_if_missing() {
  local label="$1"
  local file="$2"
  printf "  %-55s " "$label"
  if [ -f "$file" ]; then
    echo "✓"
    PASS=$((PASS+1))
  else
    echo "⚠ ($file tidak ada)"
    WARN=$((WARN+1))
  fi
}

NEW_PAGE="frontend-admin/src/app/(protected)/contracts/new/page.tsx"
EDIT_PAGE="frontend-admin/src/app/(protected)/contracts/[cn]/edit/page.tsx"

echo "═══ AUTO QA — ISSUE #1 (Tooltip bilingual) ═══"
echo ""

echo "── 1. FILE EXISTENCE ──"
warn_if_missing "Komponen Tooltip ada" \
  "frontend-admin/src/components/ui/tooltip.tsx"
warn_if_missing "field-help.ts ada" \
  "frontend-admin/src/lib/field-help.ts"

echo ""
echo "── 2. DEPENDENCIES ──"
check "@radix-ui/react-tooltip ada di package.json" \
  "grep -q '@radix-ui/react-tooltip' frontend-admin/package.json"
check "Lockfile mengandung react-tooltip" \
  "grep -q '@radix-ui/react-tooltip' frontend-admin/package-lock.json"

echo ""
echo "── 3. CODE INTEGRATION ──"
check "Tooltip diimport di new/page.tsx" \
  "grep -q 'components/ui/tooltip' '$NEW_PAGE'"
check "Tooltip diimport di edit/page.tsx" \
  "grep -q 'components/ui/tooltip' '$EDIT_PAGE'"
check "COLUMN_FLAG_HELP diimport di new/page.tsx" \
  "grep -q 'COLUMN_FLAG_HELP' '$NEW_PAGE'"
check "COLUMN_FLAG_HELP diimport di edit/page.tsx" \
  "grep -q 'COLUMN_FLAG_HELP' '$EDIT_PAGE'"
check "TooltipProvider digunakan di new/page.tsx" \
  "grep -q 'TooltipProvider' '$NEW_PAGE'"
check "TooltipProvider digunakan di edit/page.tsx" \
  "grep -q 'TooltipProvider' '$EDIT_PAGE'"
check "aria-label a11y di new/page.tsx" \
  "grep -q 'aria-label' '$NEW_PAGE'"
check "aria-label a11y di edit/page.tsx" \
  "grep -q 'aria-label' '$EDIT_PAGE'"

echo ""
echo "── 4. KAMUS TERJEMAHAN (COLUMN_FLAG_HELP) ──"
for term in is_primary is_nullable is_pii is_mandatory; do
  check "field-help: $term punya description" \
    "grep -A1 '$term:' frontend-admin/src/lib/field-help.ts | grep -q description"
done

echo ""
echo "── 5. DOKUMENTASI ──"
check "docs/glossary.md ada section Atribut Kolom" \
  "grep -q 'Atribut Kolom' docs/glossary.md"
check "Glossary menyebut Primary Key" \
  "grep -q 'Primary Key' docs/glossary.md"
check "Glossary menyebut PII" \
  "grep -qE 'PII|Personal Identifiable' docs/glossary.md"

echo ""
echo "── 6. TYPESCRIPT TYPECHECK ──"
check "Typecheck frontend-admin lulus" \
  "( cd frontend-admin && npx tsc --noEmit )"

echo ""
echo "── 7. NEXT.JS BUILD VERIFICATION ──"
check "Production build sukses" \
  "( cd frontend-admin && npm run build > /tmp/build.log 2>&1 )"

echo ""
echo "═══ RINGKASAN ═══"
echo "  ✓ PASS:  $PASS"
echo "  ✗ FAIL:  $FAIL"
echo "  ⚠ WARN:  $WARN"
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "  STATUS: ✅ QA LULUS — siap buka PR"
  exit 0
else
  echo "  STATUS: ❌ QA GAGAL — investigasi $FAIL kegagalan di atas"
  exit 1
fi
