"""
Migrasi `group_access: "user"` → `"business_user"` di koleksi user (#91).

Konteks: #75 me-rename role `user` → `business_user` supaya sejajar dengan
`developer` dan tidak ambigu dengan "pengguna" secara umum. PR-A (#90)
memberlakukan dual-accept selama window migrasi; script ini adalah PR-B —
setelah dijalankan, alias `user` dihapus dari backend/frontend dan value
resmi tinggal `business_user`.

Selektif: hanya field `group_access`. Field `type` ("user" vs "sa" =
account type, konsep berbeda) TIDAK disentuh.

Idempoten + dry-run default + `--apply`. Mirror pola
migrate_stakeholder_roles.py.

Pemakaian (paling mudah, lewat Makefile target — auto-mount scripts/):

    make migrate-role-business-user            # dry-run
    make migrate-role-business-user APPLY=1    # eksekusi

Atau manual (kalau tidak pakai make):

    docker compose run --rm --user root \\
        -v $(pwd)/repository/app:/work/app \\
        -v $(pwd)/repository/scripts:/work/scripts \\
        backend python -m scripts.rename_role_user_to_business_user [--apply]

Pre-flight (lihat #91): backup koleksi user dulu, dan pastikan tidak ada
JWT lama yang belum expire (>3 jam sejak deploy PR-B, atau force logout).
"""

import argparse
import asyncio

from app.core.connection import database, col_usr

usrcollection = database[col_usr]

OLD_ROLE = "user"
NEW_ROLE = "business_user"


async def main(apply: bool) -> int:
    # Selektif ke group_access; `type: "user"` (account type) tidak disentuh.
    query = {"group_access": OLD_ROLE}

    before = await usrcollection.count_documents(query)
    already = await usrcollection.count_documents({"group_access": NEW_ROLE})
    print(f"group_access={OLD_ROLE!r}: {before} user")
    print(f"group_access={NEW_ROLE!r}: {already} user (sudah benar)")
    print(f"Mode: {'EKSEKUSI' if apply else 'DRY-RUN'}\n")

    if before == 0:
        print("✓ Tidak ada user beralias lama — tidak ada yang dimigrasi.")
        return 0

    cursor = usrcollection.find(query, {"_id": 0, "username": 1, "name": 1})
    for u in await cursor.to_list(None):
        print(f"  - {u.get('username', '<no-username>')} ({u.get('name', '-')}): "
              f"{OLD_ROLE} → {NEW_ROLE}")
    print()

    if not apply:
        print("(dry-run — tidak ada yang diubah. Tambah --apply untuk eksekusi.)")
        return 0

    result = await usrcollection.update_many(
        query, {"$set": {"group_access": NEW_ROLE}}
    )
    after_old = await usrcollection.count_documents(query)
    after_new = await usrcollection.count_documents({"group_access": NEW_ROLE})
    print(f"✓ {result.modified_count} user diperbarui.")
    print(f"  Sisa group_access={OLD_ROLE!r}: {after_old} (harus 0)")
    print(f"  Total group_access={NEW_ROLE!r}: {after_new}")
    return 0 if after_old == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrasi group_access 'user' → 'business_user' (#91, PR-B dari #75).",
    )
    parser.add_argument("--apply", action="store_true",
                        help="Eksekusi update (default: dry-run).")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(apply=args.apply)))
