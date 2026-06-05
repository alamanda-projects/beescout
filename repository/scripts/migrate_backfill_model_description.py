"""
Backfill model[].description untuk kontrak legacy (#102 PR-B slice 4).

Konteks: slice 4 menjadikan `model.description` (deskripsi kolom) wajib di
write-path (`/datacontract/add` & `/update`) + FE zod. Kontrak legacy yang
kolomnya belum berdeskripsi akan gagal disimpan saat di-edit. Migrasi ini
mengisi description kosong dengan **penanda** dari `business_name`/nama kolom
supaya kontrak legacy tidak ke-block — steward melengkapi bertahap.

Penanda sengaja mengandung frasa "mohon dilengkapi" agar mudah dicari:
kolom yang masih perlu deskripsi manusiawi bisa di-grep / difilter di UI.

Untuk tiap kontrak yang punya `model[]`:
- Untuk tiap kolom ber-`column` (name) yang `description`-nya kosong/absen:
  set `description = "(Otomatis dari nama: <business_name|column>) — mohon dilengkapi"`.
- Kolom yang sudah punya description → dilewati (idempoten).

Idempoten — aman dijalankan ulang (run kedua = 0 perubahan). Dry-run default;
`--apply` untuk menulis. Mirror pola scripts/migrate_consumer_to_stakeholders.py.

Pemakaian (via container backend yang punya akses Mongo):

    make migrate-backfill-model-description           # dry-run
    make migrate-backfill-model-description APPLY=1    # eksekusi
"""

import argparse
import asyncio

from app.core.connection import database, col_dgr

dccollection = database[col_dgr]


def _needs_backfill(col: dict) -> bool:
    """Kolom ber-name yang description-nya kosong/absen."""
    return bool(col.get("column")) and not (col.get("description") or "").strip()


def _backfill_value(col: dict) -> str:
    base = (col.get("business_name") or col.get("column") or "kolom").strip()
    return f"(Otomatis dari nama: {base}) — mohon dilengkapi"


async def main(apply: bool) -> int:
    cursor = dccollection.find(
        {"model": {"$exists": True, "$ne": []}},
        {"_id": 1, "contract_number": 1, "model": 1},
    )
    contracts = await cursor.to_list(None)

    if not contracts:
        print("✓ Tidak ada kontrak dengan model[] non-kosong — tidak ada yang dimigrasi.")
        return 0

    print(f"Ditemukan {len(contracts)} kontrak dengan model[] non-kosong.")
    print(f"Mode: {'EKSEKUSI' if apply else 'DRY-RUN'}\n")

    changed = 0
    cols_total = 0

    for c in contracts:
        cn = c.get("contract_number", "<no-cn>")
        model = c.get("model") or []
        patched = []
        n = 0
        for col in model:
            if _needs_backfill(col):
                col = {**col, "description": _backfill_value(col)}
                n += 1
            patched.append(col)

        if n == 0:
            continue

        print(f"  - {cn}: +{n} deskripsi kolom di-backfill")
        if apply:
            await dccollection.update_one(
                {"_id": c["_id"]},
                {"$set": {"model": patched}},
            )
        changed += 1
        cols_total += n

    print()
    if apply:
        print(f"✓ {changed} kontrak diperbarui, {cols_total} deskripsi kolom di-backfill.")
        print("⚠  Deskripsi auto bertanda 'mohon dilengkapi' — minta steward melengkapi.")
    else:
        print("(dry-run — tidak ada yang diubah. Tambah --apply untuk eksekusi.)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Backfill model[].description kosong dengan penanda dari nama kolom "
            "untuk kontrak legacy (#102 PR-B slice 4)."
        ),
    )
    parser.add_argument("--apply", action="store_true",
                        help="Eksekusi update (default: dry-run).")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(apply=args.apply)))
