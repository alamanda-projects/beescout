#!/usr/bin/env bash
# QA — Issue #4: Pisah impact + severity
#
# Verifikasi bahwa semua perubahan untuk split impact/severity sudah ada
# dan TypeScript compile bersih.
#
# Jalankan dari root repo:
#   bash scripts/qa-issue-4.sh
#
# Exit 0 jika semua pass, 1 jika ada yang gagal.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0
echo "── QA: issue #4 — impact + severity split ──────────────────────"

check() {
  local desc="$1"; local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "✓ $desc"
  else
    echo "✗ $desc"
    FAIL=$((FAIL+1))
  fi
}

# ── Backend ──────────────────────────────────────────────────────────────
check "model.py: severity field ada" \
  "grep -q 'severity: Optional\[str\]' repository/app/model/model.py"

check "metadata.py: severity field ada" \
  "grep -q 'severity: Optional\[str\]' repository/app/model/metadata.py"

check "migration script ada" \
  "test -f repository/scripts/migrate_impact_severity.py"

check "migration script: logika high→severity=high ada" \
  "grep -q '\"high\".*\"high\"' repository/scripts/migrate_impact_severity.py"

# ── Frontend types ────────────────────────────────────────────────────────
check "admin rule_catalog: SeverityType export ada" \
  "grep -q 'export type SeverityType' frontend-admin/src/types/rule_catalog.ts"

check "admin rule_catalog: ImpactType tidak lagi punya high/low" \
  "! grep -q \"'high' | 'low'\" frontend-admin/src/types/rule_catalog.ts"

check "admin rule_catalog: SEVERITY_LABELS ada" \
  "grep -q 'SEVERITY_LABELS' frontend-admin/src/types/rule_catalog.ts"

check "user rule_catalog: SeverityType export ada" \
  "grep -q 'export type SeverityType' frontend-user/src/types/rule_catalog.ts"

check "admin contract.ts: severity field ada" \
  "grep -q 'severity\?' frontend-admin/src/types/contract.ts"

check "user contract.ts: severity field ada" \
  "grep -q 'severity\?' frontend-user/src/types/contract.ts"

# ── Frontend components ───────────────────────────────────────────────────
check "admin QualityRulesEditor: severity state ada" \
  "grep -q 'setSeverity' frontend-admin/src/components/quality/QualityRulesEditor.tsx"

check "admin QualityRulesEditor: SEVERITY_BIZ_LABELS dipakai" \
  "grep -q 'SEVERITY_BIZ_LABELS' frontend-admin/src/components/quality/QualityRulesEditor.tsx"

check "user QualityRulesEditor: severity state ada" \
  "grep -q 'setSeverity' frontend-user/src/components/quality/QualityRulesEditor.tsx"

# ── Form schemas ──────────────────────────────────────────────────────────
check "admin new/page.tsx: severity di zod schema" \
  "grep -q 'severity: z.string' frontend-admin/src/app/\(protected\)/contracts/new/page.tsx"

check "user new/page.tsx: severity di zod schema" \
  "grep -q 'severity: z.string' frontend-user/src/app/\(protected\)/contracts/new/page.tsx"

check "admin edit/page.tsx: severity di zod schema" \
  "grep -q 'severity: z.string' frontend-admin/src/app/\(protected\)/contracts/\[cn\]/edit/page.tsx"

# ── Docs ──────────────────────────────────────────────────────────────────
check "ADR-0003 ada" \
  "test -f docs/adr/0003-impact-severity-split.md"

check "full.yaml: severity field ada di contoh" \
  "grep -q 'severity: medium' data-contract/examples/full.yaml"

# ── TypeScript compile ────────────────────────────────────────────────────
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
