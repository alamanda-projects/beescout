"""
Migrasi kontrak legacy: backfill stakeholders[] dari metadata.consumer[].

Konteks: ADR-0007 Phase 2 (#94) — setelah Phase 1 (PR #104) mengubah filter
visibilitas untuk derive dari `stakeholders[role IN (consumer, producer)]`,
kontrak legacy yang hanya punya `metadata.consumer[]` masih bekerja via
fallback. Migrasi ini menambah stakeholder entry yang setara sehingga
fallback bisa di-drop di Phase 3.

Untuk tiap kontrak yang punya `metadata.consumer[]` non-kosong:
1. Untuk tiap `consumer[].name`, cari semua user **aktif** dengan
   `data_domain == name`.
2. Tambah ke `stakeholders[]` entry baru ber-role `consumer` dengan
   `username` user tsb — **bila belum ada** entry dengan
   (role=consumer, username=user.username).
3. Bila tidak ada user matching: warning ke stdout (kemungkinan tim
   sudah bubar atau typo — perlu invistigasi manual).

Idempoten — aman dijalankan ulang. Dry-run default; `--apply` untuk
benar-benar menulis. Mirror pola scripts/migrate_approval_roles.py &
scripts/dedupe_contracts.py.

Pemakaian (di host yang punya akses ke Mongo, via container backend):

    docker compose run --rm backend python -m scripts.migrate_consumer_to_stakeholders          # dry-run
    docker compose run --rm backend python -m scripts.migrate_consumer_to_stakeholders --apply  # eksekusi
"""

import argparse
import asyncio
from typing import Optional

from app.core.connection import database, col_dgr, col_usr

dccollection = database[col_dgr]
usrcollection = database[col_usr]


def _has_consumer_stakeholder(stakeholders: list, username: str) -> bool:
    """Cek apakah stakeholders[] sudah punya entry (role=consumer, username)."""
    for s in stakeholders or []:
        if s.get("role") == "consumer" and s.get("username") == username:
            return True
    return False


async def _users_for_team(team_name: str) -> list:
    """Daftar user aktif yang data_domain-nya sama dengan team_name."""
    cursor = usrcollection.find(
        {"data_domain": team_name, "is_active": True, "type": {"$ne": "sa"}},
        {"_id": 0, "username": 1, "name": 1},
    )
    return await cursor.to_list(None)


async def main(apply: bool) -> int:
    cursor = dccollection.find(
        {"metadata.consumer": {"$exists": True, "$ne": []}},
        {"_id": 1, "contract_number": 1, "metadata.consumer": 1, "metadata.stakeholders": 1},
    )
    contracts = await cursor.to_list(None)

    if not contracts:
        print("✓ Tidak ada kontrak dengan metadata.consumer[] non-kosong — tidak ada yang dimigrasi.")
        return 0

    print(f"Ditemukan {len(contracts)} kontrak dengan consumer[] non-kosong.")
    print(f"Mode: {'EKSEKUSI' if apply else 'DRY-RUN'}\n")

    changed = 0
    added_total = 0
    warnings: list[str] = []

    for c in contracts:
        cn = c.get("contract_number", "<no-cn>")
        consumers = (c.get("metadata") or {}).get("consumer") or []
        stakeholders = (c.get("metadata") or {}).get("stakeholders") or []
        new_entries = []

        for cons in consumers:
            team = cons.get("name")
            if not team:
                continue
            users = await _users_for_team(team)
            if not users:
                warnings.append(
                    f"  ! {cn}: tidak ada user aktif dengan data_domain={team!r} — "
                    f"consumer entry ini perlu invistigasi manual."
                )
                continue
            for u in users:
                username = u.get("username")
                if not username or _has_consumer_stakeholder(stakeholders, username):
                    continue
                new_entries.append({
                    "name": u.get("name") or username,
                    "role": "consumer",
                    "username": username,
                })
                # tandai supaya loop user berikutnya untuk tim lain tidak duplikat
                stakeholders = stakeholders + [{"role": "consumer", "username": username}]

        if not new_entries:
            continue

        names_added = [f"{e['username']} ({e['name']})" for e in new_entries]
        print(f"  - {cn}: +{len(new_entries)} stakeholder consumer: {', '.join(names_added)}")

        if apply:
            await dccollection.update_one(
                {"_id": c["_id"]},
                {"$push": {"metadata.stakeholders": {"$each": new_entries}}},
            )
        changed += 1
        added_total += len(new_entries)

    print()
    if warnings:
        print(f"Warning ({len(warnings)}):")
        for w in warnings:
            print(w)
        print()

    if apply:
        print(f"✓ {changed} kontrak diperbarui, {added_total} stakeholder ditambahkan.")
    else:
        print("(dry-run — tidak ada yang diubah. Tambah --apply untuk eksekusi.)")
    if warnings:
        print("⚠  Lihat daftar warning di atas — perlu invistigasi manual.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Backfill stakeholders[role=consumer] dari metadata.consumer[] untuk "
            "kontrak legacy (ADR-0007 Phase 2, #94)."
        ),
    )
    parser.add_argument("--apply", action="store_true",
                        help="Eksekusi update (default: dry-run).")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(apply=args.apply)))
