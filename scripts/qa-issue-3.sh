#!/usr/bin/env bash
# Auto QA/QC untuk Issue #3 — Helper text & glossary untuk Tipe Data Bisnis ↔ Teknis
# https://github.com/alamanda-projects/beescout/issues/3
#
# Dijalankan dari root repo:
#   bash scripts/qa-issue-3.sh
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

NEW_PAGE="frontend-admin/src/app/(protected)/contracts/new/page.tsx"
EDIT_PAGE="frontend-admin/src/app/(protected)/contracts/[cn]/edit/page.tsx"
FIELD_HELP="frontend-admin/src/lib/field-help.ts"
GLOSSARY="docs/glossary.md"

echo "═══ AUTO QA — ISSUE #3 (Tipe Data Guidance) ═══"
echo ""

echo "── 1. KAMUS HELPER (field-help.ts) ──"
check "DATA_TYPE_HELP diekspor" \
  "grep -q 'export const DATA_TYPE_HELP' '$FIELD_HELP'"
check "Entri logical (Tipe Bisnis) ada" \
  "grep -A2 'DATA_TYPE_HELP' '$FIELD_HELP' | grep -q 'logical'"
check "Entri physical (Tipe Teknis) ada" \
  "grep -q 'physical:' '$FIELD_HELP'"
check "Contoh logical menyebut 'Tanggal'" \
  "grep -A3 'logical:' '$FIELD_HELP' | grep -q 'Tanggal'"
check "Contoh physical menyebut 'VARCHAR'" \
  "grep -A3 'physical:' '$FIELD_HELP' | grep -q 'VARCHAR'"

echo ""
echo "── 2. INTEGRASI FORM ──"
for f in "$NEW_PAGE" "$EDIT_PAGE"; do
  short=$(echo "$f" | sed 's|frontend-admin/src/app/(protected)/contracts/||')
  check "DATA_TYPE_HELP di-import ($short)" \
    "grep -q 'DATA_TYPE_HELP' '$f'"
  check "Helper examples dipakai ($short)" \
    "grep -q 'DATA_TYPE_HELP.logical.examples' '$f' && grep -q 'DATA_TYPE_HELP.physical.examples' '$f'"
  check "Tooltip Tipe Bisnis ada ($short)" \
    "grep -q 'aria-label=\"Penjelasan Tipe Data Bisnis\"' '$f'"
  check "Tooltip Tipe Teknis ada ($short)" \
    "grep -q 'aria-label=\"Penjelasan Tipe Data Teknis\"' '$f'"
done

echo ""
echo "── 3. GLOSSARY ──"
check "Section 'Mapping Tipe Bisnis' ada" \
  "grep -q 'Mapping Tipe Bisnis' '$GLOSSARY'"
check "Tabel menyebut DECIMAL untuk Jumlah Uang" \
  "grep -q 'DECIMAL(15,2)' '$GLOSSARY'"
check "Tabel menyebut UUID untuk Identifier" \
  "grep -q 'UUID' '$GLOSSARY'"
check "Tabel menyebut DATE untuk Tanggal" \
  "grep -q 'DATE' '$GLOSSARY'"
check "Bagian Atribut Kolom tetap utuh (renamed G.)" \
  "grep -q 'G. Atribut Kolom' '$GLOSSARY'"

echo ""
echo "── 4. TYPESCRIPT TYPECHECK ──"
check "Typecheck frontend-admin lulus" \
  "( cd frontend-admin && npx tsc --noEmit )"

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
