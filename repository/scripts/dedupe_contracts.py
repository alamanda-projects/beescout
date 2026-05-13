"""
Dedup koleksi `dgr` di MongoDB.

Konteks: Issue #10 / #12 — sebelum unique index ditambahkan, endpoint
`/datacontract/add` bisa membuat dokumen ganda dengan `contract_number`
yang sama (akibat Enter-key auto-submit di form). Script ini:

1. Mengelompokkan dokumen `dgr` berdasarkan `contract_number`
2. Untuk tiap grup duplikat, **mempertahankan dokumen tertua** (ObjectId terkecil
   = waktu insert paling awal) dan menghapus sisanya
3. Idempoten — jalankan ulang tanpa side effect

Pemakaian (di host yang punya akses ke Mongo):

    cd repository
    python -m scripts.dedupe_contracts             # dry-run (default)
    python -m scripts.dedupe_contracts --apply     # benar-benar hapus
"""

import argparse
import asyncio

from app.core.connection import dccollection


async def find_duplicates() -> list[dict]:
    pipeline = [
        {"$group": {
            "_id": "$contract_number",
            "ids": {"$push": "$_id"},
            "count": {"$sum": 1},
        }},
        {"$match": {"count": {"$gt": 1}}},
    ]
    return [doc async for doc in dccollection.aggregate(pipeline)]


async def main(apply: bool) -> None:
    groups = await find_duplicates()
    if not groups:
        print("✓ Tidak ada duplikat. Koleksi sudah bersih.")
        return

    total_excess = sum(g["count"] - 1 for g in groups)
    print(f"Ditemukan {len(groups)} contract_number duplikat, total {total_excess} dokumen redundant.")

    for g in groups:
        ids_sorted = sorted(g["ids"])  # ObjectId sortable by insertion time
        keep, drop = ids_sorted[0], ids_sorted[1:]
        print(f"  contract_number={g['_id']!r}: keep {keep}, drop {len(drop)}")
        if apply:
            await dccollection.delete_many({"_id": {"$in": drop}})

    if apply:
        print(f"✓ Dihapus {total_excess} dokumen duplikat.")
    else:
        print("(dry-run — tidak ada yang dihapus. Tambah --apply untuk eksekusi.)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dedup koleksi `dgr` berdasar contract_number")
    parser.add_argument("--apply", action="store_true", help="Benar-benar hapus duplikat (default: dry-run)")
    args = parser.parse_args()
    asyncio.run(main(apply=args.apply))
