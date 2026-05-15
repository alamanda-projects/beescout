"""
migrate_impact_severity.py

Migrasi data: pisah field 'impact' menjadi 'impact' + 'severity'.

Logika migrasi:
  impact='high'        → impact='operational', severity='high'
  impact='low'         → impact='operational', severity='low'
  impact='operational' → impact='operational', severity='medium' (default)
  impact=lainnya       → tidak diubah, severity tidak diset

Idempoten: dokumen yang sudah punya field 'severity' tidak diproses ulang.

Jalankan:
  python -m scripts.migrate_impact_severity [--apply]

Tanpa --apply: hanya preview jumlah dokumen yang akan dimigrasi (dry run).
Dengan --apply: migrasi dijalankan ke database.
"""

import asyncio
import argparse
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv(
    "MONGODB_URL",
    "mongodb://{user}:{pw}@localhost:27017/{db}?authSource=admin".format(
        user=os.getenv("MONGODB_USER", "admin"),
        pw=os.getenv("MONGODB_PASS", "changeme"),
        db=os.getenv("MONGODB_DB", "dgrdb"),
    )
)

COL_DGR = os.getenv("MONGODB_COLLECTION_DGR", "dgr")

# nilai lama impact yang mencampur jenis + severity
LEGACY_SEVERITY_MAP = {
    "high": ("operational", "high"),
    "low":  ("operational", "low"),
}
DEFAULT_SEVERITY = "medium"


def derive_new_fields(old_impact: str | None) -> tuple[str | None, str | None]:
    """Return (new_impact, new_severity) given an old impact value."""
    if old_impact is None:
        return None, None
    if old_impact in LEGACY_SEVERITY_MAP:
        return LEGACY_SEVERITY_MAP[old_impact]
    if old_impact == "operational":
        return "operational", DEFAULT_SEVERITY
    return old_impact, None


def migrate_quality_list(rules: list | None) -> tuple[list, int]:
    """Migrate a list of quality rules. Returns (updated_list, changed_count)."""
    if not rules:
        return rules, 0
    changed = 0
    updated = []
    for rule in rules:
        if "severity" in rule:
            updated.append(rule)
            continue
        new_impact, new_severity = derive_new_fields(rule.get("impact"))
        new_rule = dict(rule)
        if new_impact is not None:
            new_rule["impact"] = new_impact
        if new_severity is not None:
            new_rule["severity"] = new_severity
            changed += 1
        updated.append(new_rule)
    return updated, changed


async def run(apply: bool) -> None:
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.get_default_database()
    col = db[COL_DGR]

    cursor = col.find({})
    total = 0
    migrated = 0

    async for doc in cursor:
        total += 1
        changed = 0

        # dataset-level quality
        if "metadata" in doc and "quality" in doc["metadata"]:
            new_q, n = migrate_quality_list(doc["metadata"]["quality"])
            if n:
                doc["metadata"]["quality"] = new_q
                changed += n

        # column-level quality
        for col_def in doc.get("model", []):
            if "quality" in col_def:
                new_q, n = migrate_quality_list(col_def["quality"])
                if n:
                    col_def["quality"] = new_q
                    changed += n

        if changed == 0:
            continue

        migrated += 1
        if apply:
            await col.replace_one({"_id": doc["_id"]}, doc)
            print(f"  migrated: {doc.get('contract_number', doc['_id'])} ({changed} rule(s))")
        else:
            print(f"  [dry-run] would migrate: {doc.get('contract_number', doc['_id'])} ({changed} rule(s))")

    client.close()

    print()
    print(f"Total contracts scanned : {total}")
    print(f"Contracts to migrate    : {migrated}")
    if not apply:
        print("Run with --apply to execute.")
    else:
        print("Migration complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Terapkan migrasi ke database")
    args = parser.parse_args()
    asyncio.run(run(apply=args.apply))
