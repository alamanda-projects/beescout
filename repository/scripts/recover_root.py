"""
Break-glass recovery untuk akun root BeeScout.

Konteks: Issue #59 / #61 — sejak `/setup` mengunci diri (409) begitu ada root
aktif, tidak ada lagi jalan masuk bila kredensial root hilang. Endpoint HTTP
untuk recovery sengaja TIDAK dibuat — itu sama dengan pintu belakang
account-takeover. Pemulihan harus *out-of-band*: hanya pihak yang sudah
mengontrol server (akses shell) yang boleh menjalankannya.

Trust boundary script ini = akses shell ke host / container backend.

Apa yang dilakukan:

1. Mode **recovery** — username sudah ada & ber-role root → reset password +
   pastikan aktif.
2. Mode **create** — username belum ada → buat akun root baru
   (butuh --name; --data-domain opsional).
3. Selalu menjaga invariant "tepat satu root aktif" (#59): SEMUA dokumen root
   lain di-non-aktifkan (`is_active=false`).
4. Stempel audit (`recovered_at`, `recovery_note`) pada dokumen root + ringkasan
   ke stdout (tertangkap log Docker).

Idempoten — aman dijalankan ulang. Dry-run secara default; butuh `--apply`
untuk benar-benar menulis ke DB (mirror pola scripts/dedupe_contracts.py).

Pemakaian (di host yang punya akses ke Mongo):

    # di dalam direktori repository/, atau via Docker:
    docker compose run --rm backend python -m scripts.recover_root \
        --username root --name "Root User"                 # dry-run
    docker compose run --rm backend python -m scripts.recover_root \
        --username root --name "Root User" --apply          # eksekusi

Password diminta lewat prompt tanpa echo (ketik 2x untuk konfirmasi). Untuk
pemakaian non-interaktif bisa pakai --password, tapi hindari bila bisa —
password akan tercatat di shell history.
"""

import argparse
import asyncio
import getpass
import sys
from datetime import datetime
from typing import Optional

from app.core.connection import database, col_usr, col_dom
from app.core.hasher import Hasher

usrcollection = database[col_usr]
domcollection = database[col_dom]

# Sinkron dengan seed_default_domains() di app/main.py. Diduplikasi di sini
# karena script bisa dijalankan tanpa proses FastAPI yang sudah booting —
# nilainya kecil (4 baris), tidak layak modul shared khusus.
_DEFAULT_DOMAINS = [
    {"name": "root",  "label": "Root"},
    {"name": "admin", "label": "Admin"},
]


async def _seed_default_domains(now: datetime) -> int:
    inserted = 0
    for spec in _DEFAULT_DOMAINS:
        if await domcollection.find_one({"name": spec["name"]}):
            continue
        await domcollection.insert_one({
            "name":        spec["name"],
            "label":       spec["label"],
            "description": "",
            "is_active":   True,
            "is_default":  True,
            "created_at":  now,
        })
        inserted += 1
    return inserted

# Aturan password — identik dengan /setup & /user/create di app/main.py.
_VALID_SPECIAL = set("!@#$%^&*()-_+={}[]<>,./?;:'\"")


def validate_password(pwd: str) -> Optional[str]:
    """Kembalikan pesan error bila password lemah, atau None bila lolos."""
    if len(pwd) < 8:
        return "Password minimal 8 karakter."
    if not any(c.isupper() for c in pwd):
        return "Password harus mengandung huruf besar."
    if not any(c.islower() for c in pwd):
        return "Password harus mengandung huruf kecil."
    if not any(c.isdigit() for c in pwd):
        return "Password harus mengandung angka."
    if not any(c in _VALID_SPECIAL for c in pwd):
        return "Password harus mengandung karakter khusus."
    return None


def prompt_password() -> str:
    """Minta password 2x tanpa echo sampai cocok & valid."""
    while True:
        pwd = getpass.getpass("Password root baru: ")
        err = validate_password(pwd)
        if err:
            print(f"  ✗ {err}")
            continue
        confirm = getpass.getpass("Ulangi password    : ")
        if pwd != confirm:
            print("  ✗ Password tidak cocok, ulangi.")
            continue
        return pwd


async def main(args: argparse.Namespace) -> int:
    apply = args.apply
    mode_label = "EKSEKUSI" if apply else "DRY-RUN"
    print(f"=== recover_root [{mode_label}] ===")

    # Password: dari flag (non-interaktif) atau prompt.
    if args.password is not None:
        err = validate_password(args.password)
        if err:
            print(f"✗ Password yang diberikan lewat --password ditolak: {err}")
            return 1
        password = args.password
    elif apply:
        password = prompt_password()
    else:
        password = None  # dry-run tanpa --password: tidak perlu password

    target = await usrcollection.find_one({"username": args.username})

    # Mode create butuh --name.
    if target is None and not args.name:
        print(f"✗ User '{args.username}' belum ada (mode create) — wajib sertakan --name.")
        return 1

    # Jangan diam-diam mempromosikan akun non-root jadi root.
    if target is not None and target.get("group_access") != "root":
        print(
            f"✗ User '{args.username}' ada tapi ber-role "
            f"'{target.get('group_access')}', bukan root. "
            "Pilih username root yang ada, atau username baru untuk mode create."
        )
        return 1

    # Service account bukan akun login manusia.
    if target is not None and target.get("type") == "sa":
        print(f"✗ '{args.username}' adalah service account, bukan user.")
        return 1

    is_recovery = target is not None
    other_roots = [
        u async for u in usrcollection.find({"group_access": "root"})
        if u.get("username") != args.username
    ]

    # Ringkasan rencana.
    print(f"  Mode           : {'recovery (reset akun ada)' if is_recovery else 'create (akun baru)'}")
    print(f"  Username target: {args.username}")
    print(f"  Root lain      : {len(other_roots)} dokumen → akan di-non-aktifkan")
    for u in other_roots:
        active = u.get("is_active")
        print(f"    - {u.get('username')!r} (is_active={active}) → is_active=false")

    if not apply:
        print("\n(dry-run — tidak ada perubahan. Tambah --apply untuk eksekusi.)")
        return 0

    now = datetime.now()
    note = f"break-glass via scripts.recover_root pada {now.isoformat()}"

    # 1. Non-aktifkan semua root lain — jaga invariant satu root aktif (#59).
    if other_roots:
        result = await usrcollection.update_many(
            {"group_access": "root", "username": {"$ne": args.username}},
            {"$set": {"is_active": False}},
        )
        print(f"✓ {result.modified_count} root lain di-non-aktifkan.")

    hashed = Hasher.get_password_hash(password)

    if is_recovery:
        # 2a. Reset password + aktifkan akun root yang ada.
        # Sekalian normalisasi data_domain ke 'root' supaya konsisten dengan
        # invariant baru di /setup (#74) — recovery sering dipakai justru saat
        # database lama yang nyangkut, jadi mungkin masih data_domain lama.
        await usrcollection.update_one(
            {"username": args.username},
            {"$set": {
                "password": hashed,
                "is_active": True,
                "group_access": "root",
                "data_domain": "root",
                "recovered_at": now,
                "recovery_note": note,
            }},
        )
        print(f"✓ Akun root '{args.username}' di-reset & diaktifkan.")
    else:
        # 2b. Buat akun root baru. data_domain dipaksa 'root' (#74).
        await usrcollection.insert_one({
            "username": args.username,
            "password": hashed,
            "name": args.name,
            "group_access": "root",
            "data_domain": "root",
            "is_active": True,
            "type": "user",
            "created_at": now,
            "recovered_at": now,
            "recovery_note": note,
        })
        print(f"✓ Akun root baru '{args.username}' dibuat.")

    # 3. Seed domain default ('root', 'admin') kalau belum ada (#74). Sama
    # invariant dengan /setup — recovery di DB lama yang belum punya katalog
    # domain pun ikut ter-bootstrap.
    seeded = await _seed_default_domains(now)
    if seeded:
        print(f"✓ {seeded} domain default ('root', 'admin') ditambahkan ke katalog.")

    print(f"\n✓ Selesai. Tepat satu root aktif: '{args.username}'. Silakan login.")
    print(f"  AUDIT: {note}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Break-glass recovery akun root BeeScout (jalankan dari server).",
    )
    parser.add_argument("--username", required=True, help="Username root yang dipulihkan / dibuat.")
    parser.add_argument("--name", help="Nama tampilan (wajib untuk mode create).")
    parser.add_argument("--data-domain", default="root",
                        help="DEPRECATED (#74): akun root selalu di domain 'root'. "
                             "Argumen ini diabaikan, dipertahankan untuk kompatibilitas CLI.")
    parser.add_argument("--password", help="Password baru (hindari — tercatat di shell history; "
                                           "biarkan kosong agar diminta lewat prompt aman).")
    parser.add_argument("--apply", action="store_true",
                        help="Benar-benar tulis ke DB (default: dry-run).")
    sys.exit(asyncio.run(main(parser.parse_args())))
