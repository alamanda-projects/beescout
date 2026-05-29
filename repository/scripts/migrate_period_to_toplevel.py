"""
Migrasi kontrak legacy: pindahkan `effective_date` & `end_of_contract`
dari `metadata.sla.*` ke top-level `metadata.*`, sekaligus rename
`end_of_contract` → `expiry_date`.

Konteks: #103 PR-B — `standard_version` 0.5.0 memisahkan lifecycle
kontrak dari concern SLA. PR-A (#115) merubah spec; PR-B mendukung
Pydantic shape baru + migrasi data MongoDB. PR-C akan expose FE wizard.

Untuk tiap kontrak yang punya `metadata.sla.effective_date` ATAU
`metadata.sla.end_of_contract`:

1. Promote ke top-level: `metadata.effective_date`, `metadata.expiry_date`
   (hanya kalau top-level belum terisi — top-level menang).
2. `$unset` field lama di `metadata.sla.*`.
3. Sama untuk `pending_changes.metadata.sla.*` agar approval draft
   yang menunggu vote ikut tersinkron dengan shape baru.

Idempoten — aman dijalankan ulang. Dry-run default; `--apply` untuk
benar-benar menulis. Mirror pola scripts/migrate_consumer_to_stakeholders.py.

Pemakaian:

    make migrate-period-to-toplevel           # dry-run
    make migrate-period-to-toplevel APPLY=1   # eksekusi
"""

import argparse
import asyncio

from app.core.connection import database, col_dgr

dccollection = database[col_dgr]


def _plan_promotion(
    metadata: dict | None,
) -> tuple[dict, list[str], list[str]]:
    """Hitung $set & $unset untuk satu shape (top-level metadata atau
    pending_changes.metadata). Return (set_ops, unset_paths_relative,
    notes)."""
    set_ops: dict = {}
    unset_paths: list[str] = []
    notes: list[str] = []

    if not isinstance(metadata, dict):
        return set_ops, unset_paths, notes

    sla = metadata.get("sla")
    if not isinstance(sla, dict):
        return set_ops, unset_paths, notes

    legacy_eff = sla.get("effective_date")
    legacy_end = sla.get("end_of_contract")

    if legacy_eff is not None:
        unset_paths.append("sla.effective_date")
        if not metadata.get("effective_date"):
            set_ops["effective_date"] = legacy_eff
        else:
            notes.append(
                f"top-level effective_date sudah ada ({metadata['effective_date']!r}) — "
                f"sla.effective_date ({legacy_eff!r}) di-drop saja."
            )

    if legacy_end is not None:
        unset_paths.append("sla.end_of_contract")
        if not metadata.get("expiry_date"):
            set_ops["expiry_date"] = legacy_end
        else:
            notes.append(
                f"top-level expiry_date sudah ada ({metadata['expiry_date']!r}) — "
                f"sla.end_of_contract ({legacy_end!r}) di-drop saja."
            )

    return set_ops, unset_paths, notes


def _build_mongo_ops(
    metadata: dict | None,
    pending_metadata: dict | None,
) -> tuple[dict, dict, list[str]]:
    """Bangun $set & $unset gabungan untuk metadata + pending_changes.metadata."""
    set_doc: dict = {}
    unset_doc: dict = {}
    all_notes: list[str] = []

    s, u, n = _plan_promotion(metadata)
    for k, v in s.items():
        set_doc[f"metadata.{k}"] = v
    for path in u:
        unset_doc[f"metadata.{path}"] = ""
    all_notes.extend(n)

    s, u, n = _plan_promotion(pending_metadata)
    for k, v in s.items():
        set_doc[f"pending_changes.metadata.{k}"] = v
    for path in u:
        unset_doc[f"pending_changes.metadata.{path}"] = ""
    all_notes.extend([f"(pending) {note}" for note in n])

    return set_doc, unset_doc, all_notes


async def main(apply: bool) -> int:
    # Cari kontrak yang punya legacy field di salah satu lokasi (top-level
    # metadata atau di dalam pending_changes).
    query = {
        "$or": [
            {"metadata.sla.effective_date": {"$exists": True}},
            {"metadata.sla.end_of_contract": {"$exists": True}},
            {"pending_changes.metadata.sla.effective_date": {"$exists": True}},
            {"pending_changes.metadata.sla.end_of_contract": {"$exists": True}},
        ]
    }
    cursor = dccollection.find(
        query,
        {
            "_id": 1,
            "contract_number": 1,
            "metadata.effective_date": 1,
            "metadata.expiry_date": 1,
            "metadata.sla": 1,
            "pending_changes.metadata.effective_date": 1,
            "pending_changes.metadata.expiry_date": 1,
            "pending_changes.metadata.sla": 1,
        },
    )
    contracts = await cursor.to_list(None)

    if not contracts:
        print(
            "✓ Tidak ada kontrak dengan metadata.sla.effective_date / end_of_contract "
            "(atau di pending_changes) — tidak ada yang dimigrasi."
        )
        return 0

    print(f"Ditemukan {len(contracts)} kontrak dengan legacy period field.")
    print(f"Mode: {'EKSEKUSI' if apply else 'DRY-RUN'}\n")

    changed = 0
    all_warnings: list[str] = []

    for c in contracts:
        cn = c.get("contract_number", "<no-cn>")
        metadata = c.get("metadata") or {}
        pending = (c.get("pending_changes") or {}).get("metadata")

        set_doc, unset_doc, notes = _build_mongo_ops(metadata, pending)

        if not set_doc and not unset_doc:
            # Sudah ter-migrasi sebelumnya (top-level isi, sla kosong).
            continue

        summary = []
        if set_doc:
            summary.append(f"$set {list(set_doc.keys())}")
        if unset_doc:
            summary.append(f"$unset {list(unset_doc.keys())}")
        print(f"  - {cn}: {'; '.join(summary)}")
        for note in notes:
            all_warnings.append(f"    ! {cn}: {note}")

        if apply:
            update_doc = {}
            if set_doc:
                update_doc["$set"] = set_doc
            if unset_doc:
                update_doc["$unset"] = unset_doc
            await dccollection.update_one({"_id": c["_id"]}, update_doc)
        changed += 1

    print()
    if all_warnings:
        print(f"Catatan ({len(all_warnings)}):")
        for w in all_warnings:
            print(w)
        print()

    if apply:
        print(f"✓ {changed} kontrak diperbarui.")
    else:
        print("(dry-run — tidak ada yang diubah. Tambah --apply untuk eksekusi.)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Pindahkan `effective_date` & `end_of_contract` dari metadata.sla.* ke "
            "metadata top-level (rename `end_of_contract` → `expiry_date`). "
            "Standard 0.5.0 (#103)."
        ),
    )
    parser.add_argument("--apply", action="store_true",
                        help="Eksekusi update (default: dry-run).")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(apply=args.apply)))
