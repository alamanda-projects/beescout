"""
Migrasi `metadata.stakeholders[*].role` ke 4 nilai spec BeeScout.

Konteks: validator & FE dropdown sebelumnya allow 7 nilai (engineer,
analyst, architect, steward + 3 nilai spec lainnya minus `reviewer`).
Spec BeeScout di [data-contract/docs/README.md](../../data-contract/
docs/README.md) line 94 menetapkan 4 nilai closed:

    [owner, producer, consumer, reviewer]

Role di kontrak = fungsi user terhadap kontrak (BUKAN job title).
1 user dengan job title sama bisa beda role di kontrak berbeda.

Mapping role lama → nilai spec terdekat (fungsi):

    engineer  → producer  (engineer setup/maintain pipeline data)
    analyst   → consumer  (analyst pakai data untuk analisis)
    architect → producer  (architect design pipeline, lebih dekat producer)
    steward   → reviewer  (steward = pengawas governance)

Idempoten + dry-run default + `--apply`. Mirror pola
migrate_consumer_to_stakeholders.py.

Pemakaian:

    docker compose run --rm backend python -m scripts.migrate_stakeholder_roles          # dry-run
    docker compose run --rm backend python -m scripts.migrate_stakeholder_roles --apply  # eksekusi
"""

import argparse
import asyncio
from copy import deepcopy

from app.core.connection import database, col_dgr

dccollection = database[col_dgr]

# Mapping role lama (non-spec) → nilai spec terdekat (best-effort fungsi).
# Auto-map; admin disarankan review log per kontrak setelah --apply.
ROLE_MAP: dict[str, str] = {
    "engineer":  "producer",
    "analyst":   "consumer",
    "architect": "producer",
    "steward":   "reviewer",
}

SPEC_ROLES = {"owner", "producer", "consumer", "reviewer"}


async def main(apply: bool) -> int:
    # Cari kontrak yang punya stakeholder dengan role non-spec.
    non_spec_roles = list(ROLE_MAP.keys())
    cursor = dccollection.find(
        {"metadata.stakeholders.role": {"$in": non_spec_roles}},
        {"_id": 1, "contract_number": 1, "metadata.stakeholders": 1},
    )
    contracts = await cursor.to_list(None)

    if not contracts:
        print("✓ Tidak ada kontrak dengan role non-spec — tidak ada yang dimigrasi.")
        return 0

    print(f"Ditemukan {len(contracts)} kontrak dengan stakeholder role non-spec.")
    print(f"Mode: {'EKSEKUSI' if apply else 'DRY-RUN'}\n")

    changed = 0
    unknown_roles: dict[str, int] = {}

    for c in contracts:
        cn = c.get("contract_number", "<no-cn>")
        stakeholders = (c.get("metadata") or {}).get("stakeholders") or []
        new_stakeholders = deepcopy(stakeholders)
        per_contract_changes: list[str] = []

        for s in new_stakeholders:
            old_role = s.get("role")
            if not old_role or old_role in SPEC_ROLES:
                continue
            new_role = ROLE_MAP.get(old_role)
            if new_role is None:
                # Role asing yang tidak ter-mapping (mis. role custom).
                # Catat untuk admin review, jangan diubah.
                unknown_roles[old_role] = unknown_roles.get(old_role, 0) + 1
                continue
            s["role"] = new_role
            per_contract_changes.append(
                f"{s.get('username') or s.get('name') or '<anon>'}: "
                f"{old_role} → {new_role}"
            )

        if not per_contract_changes:
            continue

        print(f"  - {cn}: {len(per_contract_changes)} role di-map")
        for ch in per_contract_changes:
            print(f"      • {ch}")

        if apply:
            await dccollection.update_one(
                {"_id": c["_id"]},
                {"$set": {"metadata.stakeholders": new_stakeholders}},
            )
        changed += 1

    print()
    if unknown_roles:
        print("⚠ Role asing yang TIDAK ter-mapping (perlu invistigasi admin):")
        for role, count in sorted(unknown_roles.items()):
            print(f"    {role!r}: {count} stakeholder")
        print()

    if apply:
        print(f"✓ {changed} kontrak diperbarui.")
    else:
        print("(dry-run — tidak ada yang diubah. Tambah --apply untuk eksekusi.)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Migrasi metadata.stakeholders[*].role ke 4 nilai spec BeeScout "
            "(owner/producer/consumer/reviewer)."
        ),
    )
    parser.add_argument("--apply", action="store_true",
                        help="Eksekusi update (default: dry-run).")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(apply=args.apply)))
