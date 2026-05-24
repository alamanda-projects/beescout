"""
Tambah `approvers_by_role` + `fallback_roles` ke approval doc lama.

Konteks: ADR-0004 / Issue #27 — approval workflow di-restruktur agar konsensus
dihitung per peran (steward + producer + consumer). Approval baru selalu
mengisi field tersebut, tapi approval `pending` yang dibuat sebelum deploy
hanya punya field `approvers` (flat list).

Script ini idempoten:
1. Cari approval `status: pending` tanpa `approvers_by_role`.
2. Untuk tiap doc, ambil kontrak terkait dan derive ulang via
   `derive_approvers_by_role()` dari `app.main`.
3. Set field baru di-place.

Approval `approved` / `rejected` tidak disentuh — sudah selesai.

Pemakaian:

    cd repository
    python -m scripts.migrate_approval_roles             # dry-run
    python -m scripts.migrate_approval_roles --apply     # eksekusi
"""

import argparse
import asyncio

from app.core.connection import aprcollection, dccollection
from app.main import derive_approvers_by_role


async def main(apply: bool) -> None:
    cursor = aprcollection.find(
        {"status": "pending", "approvers_by_role": {"$exists": False}},
        {"_id": 1, "approval_id": 1, "contract_number": 1},
    )
    pending = await cursor.to_list(None)

    if not pending:
        print("✓ Tidak ada approval pending lama yang perlu dimigrasi.")
        return

    print(f"Ditemukan {len(pending)} approval pending tanpa approvers_by_role.")

    updated = 0
    skipped = 0
    for doc in pending:
        contract = await dccollection.find_one({"contract_number": doc["contract_number"]})
        if not contract:
            print(f"  ! {doc['approval_id']}: kontrak {doc['contract_number']!r} tidak ditemukan — skip.")
            skipped += 1
            continue

        approvers_by_role, fallback_roles = await derive_approvers_by_role(contract)
        flat = sorted({u for users in approvers_by_role.values() for u in users})

        print(f"  - {doc['approval_id']} ({doc['contract_number']}): "
              f"steward={len(approvers_by_role['steward'])}, "
              f"producer={len(approvers_by_role['producer'])}, "
              f"consumer={len(approvers_by_role['consumer'])}, "
              f"fallback={fallback_roles or 'none'}")

        if apply:
            await aprcollection.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "approvers_by_role": approvers_by_role,
                    "fallback_roles": fallback_roles,
                    "approvers": flat,
                }},
            )
            updated += 1

    if apply:
        print(f"✓ {updated} approval dimigrasi, {skipped} di-skip (kontrak hilang).")
    else:
        print("(dry-run — tidak ada yang diubah. Tambah --apply untuk eksekusi.)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backfill approvers_by_role pada approval `pending` lama (ADR-0004)."
    )
    parser.add_argument("--apply", action="store_true",
                        help="Eksekusi update (default: dry-run).")
    args = parser.parse_args()
    asyncio.run(main(apply=args.apply))
