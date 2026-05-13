#!/usr/bin/env bash
# QA — Form button safety check
#
# Cegah regresi bug "kontrak tersimpan tanpa klik Simpan" (Issue #11).
#
# HTML spec: <button> di dalam <form> tanpa atribut `type` default-nya
# bertipe `submit`. Akibatnya, tombol toggle / aksi internal di form
# (mode switcher, tab, accordion, dsb.) diam-diam ikut men-trigger
# form submit setiap kali diklik.
#
# Script ini meng-scan kedua frontend untuk:
#   (1) Raw <button> tag tanpa atribut type=
#   (2) Memastikan shadcn Button.tsx tetap punya default type="button"
#
# Jalankan dari root repo:
#   bash scripts/qa-form-buttons.sh
#
# Exit 0 jika bersih, 1 jika ada pelanggaran.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0

echo "── QA: form button safety ──────────────────────────────────────"

# ─── Check 1: Raw <button> without type= ──────────────────────────────
#
# awk meng-collect blok multi-line <button ...> sampai ketemu '>'.
# Jika blok tidak mengandung 'type=' (literal string atau JSX expr),
# laporkan sebagai pelanggaran.

scan_raw_buttons() {
  local dir="$1"
  find "$dir/src" -name "*.tsx" -print0 2>/dev/null | while IFS= read -r -d '' f; do
    awk -v file="$f" '
      /<button/ { collecting=1; start_line=NR; ctx="" }
      collecting { ctx = ctx $0 ORS }
      collecting && />/ {
        if (ctx !~ /type=/) {
          printf("  %s:%d\n%s\n", file, start_line, ctx)
        }
        collecting=0
        ctx=""
      }
    ' "$f"
  done
}

violations=$(
  scan_raw_buttons "frontend-admin"
  scan_raw_buttons "frontend-user"
)

if [ -n "$violations" ]; then
  echo "✗ Raw <button> tanpa atribut type= ditemukan:"
  echo "$violations" | sed 's/^/    /'
  echo ""
  echo "  Tambah type=\"button\" (atau type=\"submit\"/type=\"reset\") secara eksplisit."
  echo "  Lihat docs/contributing/form-buttons.md untuk konvensi."
  FAIL=$((FAIL+1))
else
  echo "✓ Semua raw <button> punya atribut type= eksplisit"
fi

# ─── Check 2: Shadcn Button.tsx defaults to type="button" ─────────────
#
# Pastikan defensive default tidak ter-revert. Pattern yang kita harapkan
# ada di Button.tsx adalah penurunan default ke 'button' saat type tidak
# disediakan oleh consumer.

for btn in frontend-admin/src/components/ui/button.tsx \
           frontend-user/src/components/ui/button.tsx; do
  if [ ! -f "$btn" ]; then
    echo "✗ $btn tidak ditemukan"
    FAIL=$((FAIL+1))
    continue
  fi
  # Cek tanda tangan: harus ekstrak `type` dari props dan set default ke 'button'.
  if grep -qE "type \?\? 'button'|type \?\? \"button\"" "$btn"; then
    echo "✓ $btn default type=\"button\" aktif"
  else
    echo "✗ $btn tidak men-default type=\"button\""
    echo "  Pattern yang diharapkan: type ?? 'button' (lihat docs/contributing/form-buttons.md)"
    FAIL=$((FAIL+1))
  fi
done

echo "────────────────────────────────────────────────────────────────"

if [ "$FAIL" -gt 0 ]; then
  echo "GAGAL ($FAIL check)."
  exit 1
fi

echo "OK — semua check lulus."
exit 0
