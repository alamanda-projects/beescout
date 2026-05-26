# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/main.py
# # # Function: Main script
# # # =======================

from fastapi import FastAPI, HTTPException, Depends, Request, Body, UploadFile, File
from pymongo.errors import DuplicateKeyError
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Dict
from app.model.users import UserCreate, SetupRequest
from app.model.domains import DomainCreate, DomainUpdate
from app.core.connection import database, col_usr, col_dgr, col_apr, col_dom
from app.model.rule_catalog import RuleCatalogCreate, RuleCatalogUpdate
from app.model.approval import ApprovalRecord, VoteRequest
from app.core.display import *
from app.core.hasher import Hasher
from app.core.addon_loader import (
    load_catalog_rules_addon,
    load_sample_contracts_addon,
)
from app.core.generator import (
    cn_generator,
    create_jwt_token,
    create_jwt_token_sakey,
    create_private_key,
    tkn_exp,
    sa_exp,
)
from datetime import datetime, timedelta
from app.core.verificator import (
    user_verification,
    access_verification,
    access_verification_filter,
    token_verification,
    grplvlroot,
    grplvladmin,
    grplvldev,
    grplvlall,
)
from app.info.app_info import *
from decouple import config
import random
import yaml

# Origins allowed to make cross-origin requests (comma-separated in env)
_raw_origins = config("ALLOWED_ORIGINS", default="http://localhost:3000,http://localhost:3001")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# Set to "false" only in local dev without HTTPS
COOKIE_SECURE = config("COOKIE_SECURE", default="true").lower() == "true"

# Rate limiter — key per client IP
limiter = Limiter(key_func=get_remote_address)

current_dateTime = datetime.now()

# Database declaration
usrcollection = database[col_usr]
dccollection = database[col_dgr]
catalogcollection = database["catalog_rules"]
aprcollection = database[col_apr]
domcollection = database[col_dom]

# Error response
usrnotallowed = [usr_403, usr_403_elders, usr_403_guardian]
dcnotfound = dc_404
dcnotvalid = dc_412  # # persiapan untuk validasi YAML / JSON
dc_404_notfound = HTTPException(status_code=404, detail=dcnotfound)
botnotallowed = [usr_403_optimus, usr_403_megatron, usr_403_grimlock]
hmnnotallowed = [usr_403_optimus2, usr_403_megatron2, usr_403_grimlock2]

app = FastAPI(
    title=app_title,
    description=app_description,
    summary=app_summary,
    version=app_version,
    # terms_of_service=terms_of_service,
    contact={
        "name": app_contact_name,
        "url": app_contact_url,
        "email": app_contact_email,
    },
    license_info={
        "name": app_license_info_name,
        "url": app_license_info_url,
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    # PATCH/PUT/DELETE wajib ada — tanpa ini browser memblokir preflight
    # untuk edit/nonaktifkan user, edit domain, update kontrak (issue #58).
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# ── Role-gated dependency helpers ─────────────────────────────────────────────
# These wrap token_verification so they can be used with Depends() in routes.

async def require_root(current_user: dict = Depends(token_verification)):
    await access_verification(current_user["lvl"], current_user["sts"], grplvlroot)
    return current_user


async def require_admin(current_user: dict = Depends(token_verification)):
    await access_verification(current_user["lvl"], current_user["sts"], grplvladmin)
    return current_user


async def require_any(current_user: dict = Depends(token_verification)):
    await access_verification(current_user["lvl"], current_user["sts"], grplvlall)
    return current_user


# ── Domain helpers ────────────────────────────────────────────────────────────

def slugify_domain(raw: str) -> str:
    """Normalise a domain name into a lowercase slug — the matching key."""
    return "-".join((raw or "").strip().lower().split())


# Dua domain yang selalu ada sejak hari ke-1 (issue #74):
#   `root`  — domain akun super admin (dibuat /setup)
#   `admin` — domain default tim Enterprise Data Steward
# Ditandai `is_default=True` supaya tidak bisa dinonaktifkan/dihapus.
_DEFAULT_DOMAINS = [
    {"name": "root",  "label": "Root"},
    {"name": "admin", "label": "Admin"},
]


async def seed_default_domains() -> int:
    """Idempoten: insert domain default yang belum ada. Return jumlah yang
    benar-benar diinsert (0 berarti semuanya sudah ada).

    Dipanggil oleh /setup dan _seed_root_from_env supaya katalog Domain
    tidak pernah kosong di lingkungan fresh.
    """
    inserted = 0
    now = datetime.now()
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


async def derive_approvers_by_role(contract: dict) -> tuple[Dict[str, list], list]:
    """Hitung approver per peran untuk satu kontrak (lihat ADR-0005, supersedes ADR-0004).

    Mengembalikan tuple (approvers_by_role, fallback_roles):
      - approvers_by_role: dict {"owner": [...], "producer": [...], "consumer": [...]}
      - fallback_roles: peran yang kosong → auto-pass (audit trail).

    Ketiga peran diturunkan dari `metadata.stakeholders[role,username]`.
    Admin/root tidak lagi otomatis ikut sebagai approver — governance
    sepenuhnya per-stakeholder.

    Hanya stakeholder ber-username yang **aktif** di koleksi user yang dihitung.
    Username inaktif disaring agar approval tidak nyangkut.
    """
    metadata = contract.get("metadata") or {}
    stakeholders = metadata.get("stakeholders") or []

    def _candidates(role: str) -> set:
        return {
            s["username"] for s in stakeholders
            if s.get("role") == role and s.get("username")
        }

    owner_candidates    = _candidates("owner")
    producer_candidates = _candidates("producer")
    consumer_candidates = _candidates("consumer")

    # Saring kandidat: hanya user yang masih aktif
    all_candidates = owner_candidates | producer_candidates | consumer_candidates
    active_set: set = set()
    if all_candidates:
        active_docs = await usrcollection.find(
            {"username": {"$in": list(all_candidates)}, "is_active": True},
            {"username": 1, "_id": 0},
        ).to_list(None)
        active_set = {u["username"] for u in active_docs}

    approvers_by_role = {
        "owner":    sorted(owner_candidates & active_set),
        "producer": sorted(producer_candidates & active_set),
        "consumer": sorted(consumer_candidates & active_set),
    }
    fallback_roles = [r for r, users in approvers_by_role.items() if not users]
    return approvers_by_role, fallback_roles


def is_consensus_reached(approvers_by_role: dict, votes: list) -> bool:
    """Konsensus tercapai bila tiap peran non-kosong punya >= 1 vote approved."""
    approved = {v["username"] for v in votes if v.get("vote") == "approved"}
    for users in approvers_by_role.values():
        if not users:
            continue  # peran kosong → auto-pass
        if not (set(users) & approved):
            return False
    return True


async def derive_catalog_approvers() -> tuple[Dict[str, list], list]:
    """Approver untuk pengajuan modul rule catalog (issue #69 / #27).

    Rule catalog adalah resource **global** (tidak terikat kontrak), jadi
    tata kelolanya lewat governance role steward (= admin/root aktif), bukan
    via stakeholder per-kontrak seperti ADR-0005. Konsisten dengan keputusan
    "Opsi C khusus steward-only" yang dicatat saat diskusi #27.
    """
    docs = await usrcollection.find(
        {"group_access": {"$in": grplvladmin}, "is_active": True},
        {"username": 1, "_id": 0},
    ).to_list(None)
    stewards = sorted({u["username"] for u in docs})
    approvers_by_role = {"steward": stewards}
    fallback_roles = [] if stewards else ["steward"]
    return approvers_by_role, fallback_roles


async def validate_data_domain(domain: str):
    """Ensure `data_domain` refers to an active, registered domain.

    Skipped while the `domains` collection is still empty — keeps free-text
    domains valid until an admin starts curating the catalog (backward compat,
    see issue #34). Once any domain exists, the value must match a known slug.
    """
    if not await domcollection.count_documents({}):
        return
    match = await domcollection.find_one({"name": domain, "is_active": True})
    if not match:
        raise HTTPException(
            status_code=422,
            detail=f"Domain '{domain}' tidak terdaftar atau tidak aktif. "
                   "Pilih dari katalog Domain Data.",
        )


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "version": app_version}


@app.get("/setup/status", tags=["system"])
async def setup_status():
    """Returns whether the initial root account has been created."""
    existing_root = await usrcollection.find_one({"group_access": "root", "is_active": True})
    return {"setup_complete": existing_root is not None}


@app.post("/setup", tags=["system"])
async def bootstrap_setup(user_form: SetupRequest):
    """
    Internal bootstrap endpoint used by the web setup flow to create the first root account.
    Returns 409 if a root account already exists.
    The web setup page is disabled once setup is complete.
    """
    existing_root = await usrcollection.find_one({"group_access": "root", "is_active": True})
    if existing_root:
        raise HTTPException(status_code=409, detail="Setup already complete. A root account exists.")

    if len(user_form.password) < 8:
        raise HTTPException(status_code=422, detail=pwd_422_long)

    valid_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+={}[]<>,./?;:'\""
    )
    if not any(c.isupper() for c in user_form.password):
        raise HTTPException(status_code=422, detail=pwd_422_upcase)
    if not any(c.islower() for c in user_form.password):
        raise HTTPException(status_code=422, detail=pwd_422_locase)
    if not any(c.isdigit() for c in user_form.password):
        raise HTTPException(status_code=422, detail=pwd_422_num)
    if not any(c in valid_chars for c in user_form.password if not c.isalnum()):
        raise HTTPException(status_code=422, detail=pwd_422_spc)

    hashed_password = Hasher.get_password_hash(user_form.password)

    # Jaga invariant "tepat satu root aktif": non-aktifkan semua dokumen root
    # lama yang masih tersisa sebelum membuat root baru. Kode hanya sampai sini
    # bila tidak ada root AKTIF (cek 409 di atas) — jadi yang ter-disable hanya
    # root non-aktif yang menggantung; defensif terhadap dokumen tanpa field
    # `is_active`.
    await usrcollection.update_many(
        {"group_access": "root"},
        {"$set": {"is_active": False}},
    )

    user_data = {
        "username": user_form.username,
        "password": hashed_password,
        "name": user_form.name,
        "group_access": "root",
        # Root selalu di domain "root" (#74, #84). Field ini tidak ada di
        # SetupRequest sehingga invariant tidak bisa di-bypass dari form.
        "data_domain": "root",
        "is_active": True,
        "type": "user",
        "created_at": datetime.now(),
    }
    await usrcollection.insert_one(user_data)

    # Seed domain default ('root', 'admin') jika belum ada (#74). Idempoten
    # supaya /setup yang dipanggil ulang (mis. test rerun) aman.
    await seed_default_domains()

    sample_contracts_imported = 0
    if user_form.import_sample_contracts:
        sample_contracts = load_sample_contracts_addon()
        for contract in sample_contracts:
            contract_doc = {**contract, "created_by": user_form.username}
            try:
                await dccollection.insert_one(contract_doc)
                sample_contracts_imported += 1
            except DuplicateKeyError:
                continue

    catalog_rules_imported = False
    catalog_rules_count = 0
    if user_form.import_catalog_rules:
        catalog_rules = load_catalog_rules_addon()
        if catalog_rules and await catalogcollection.count_documents({}) == 0:
            await catalogcollection.insert_many(catalog_rules)
            catalog_rules_imported = True
            catalog_rules_count = len(catalog_rules)

    return {
        "message": "Root account created. Please log in.",
        "sample_contracts_imported": sample_contracts_imported > 0,
        "sample_contracts_count": sample_contracts_imported,
        "catalog_rules_imported": catalog_rules_imported,
        "catalog_rules_count": catalog_rules_count,
    }


@app.on_event("startup")
async def ensure_indexes():
    await dccollection.create_index("contract_number", unique=True)
    await domcollection.create_index("name", unique=True)


# Auto-seed root account dari env vars saat startup (issue #32).
# Pola serupa Grafana (GF_SECURITY_ADMIN_PASSWORD) — memudahkan automated
# deployment yang tidak bisa curl /setup interaktif. Idempoten: kalau
# root aktif sudah ada, skip diam-diam. Password lemah → startup gagal
# dengan RuntimeError jelas (lebih baik fail-fast daripada akun lemah).
async def _seed_root_from_env() -> None:
    username = config("SEED_ROOT_USERNAME", default="")
    password = config("SEED_ROOT_PASSWORD", default="")
    if not username or not password:
        return  # env tidak di-set → tidak ada aksi

    # Validasi policy yang sama dengan /setup
    valid_special_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+={}[]<>,./?;:'\""
    )
    checks = [
        (len(password) < 8,                                                    pwd_422_long),
        (not any(c.isupper() for c in password),                               pwd_422_upcase),
        (not any(c.islower() for c in password),                               pwd_422_locase),
        (not any(c.isdigit() for c in password),                               pwd_422_num),
        (not any(c in valid_special_chars for c in password if not c.isalnum()), pwd_422_spc),
    ]
    for failed, message in checks:
        if failed:
            raise RuntimeError(f"SEED_ROOT_PASSWORD invalid: {message}")

    existing_root = await usrcollection.find_one(
        {"group_access": "root", "is_active": True}
    )
    if existing_root:
        return  # idempotent — root aktif sudah ada

    # Jaga invariant "tepat satu root aktif" sama seperti /setup
    await usrcollection.update_many(
        {"group_access": "root"},
        {"$set": {"is_active": False}},
    )

    hashed = Hasher.get_password_hash(password)
    await usrcollection.insert_one({
        "username":     username,
        "password":     hashed,
        "name":         config("SEED_ROOT_NAME",   default=username),
        "group_access": "root",
        # Issue #74: root selalu di domain "root". SEED_ROOT_DOMAIN sengaja
        # tidak lagi dibaca — invariant ditegakkan oleh seed_default_domains().
        "data_domain":  "root",
        "is_active":    True,
        "type":         "user",
        "created_at":   datetime.now(),
    })
    await seed_default_domains()
    print(f"[seed] Root account '{username}' created from SEED_ROOT_* env.")


@app.on_event("startup")
async def auto_seed_root():
    await _seed_root_from_env()


@app.get("/", response_class=RedirectResponse, status_code=302)
async def default_page():
    return "/welcome"


@app.get("/welcome")
async def welcome():
    with open("app/welcome_page.html", "r") as f:
        content = f.read()

        content = content.replace("{APP_TITLE}", app_title)
        content = content.replace("{APP_VERSION}", app_version)
        content = content.replace("{APP_CONTACT_NAME}", app_contact_name)
        content = content.replace("{APP_LICENSE_INFO_NAME}", app_license_info_name)
        content = content.replace("{APP_LICENSE_INFO_URL}", app_license_info_url)

    return HTMLResponse(content=content)


# Generate Token
@app.post("/login")
@limiter.limit("10/minute")
async def login_for_access_token(request: Request, credentials: dict = Body(...)):
    username = credentials.get("username")
    password = credentials.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail=random.choice(usrnotallowed))

    db_user = await usrcollection.find_one({"username": username})
    if not db_user:
        raise HTTPException(status_code=400, detail=random.choice(usrnotallowed))

    if not Hasher.verify_password(password, db_user["password"]):
        raise HTTPException(status_code=401, detail=random.choice(usrnotallowed))

    access_token_expires = tkn_exp
    access_token = create_jwt_token(
        {
            "usr": db_user["username"],
            "lvl": db_user["group_access"],
            "sts": db_user["is_active"],
            "tim": db_user["data_domain"],
            "typ": db_user["type"],
        },
        access_token_expires,
    )

    response = JSONResponse(
        content={
            "message": "Login successful",
            "user_id": str(db_user.get("username")),
            "name": db_user.get("name"),
        }
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="Strict",
        max_age=access_token_expires * 60,
    )
    return response


@app.post("/login/midware", tags=["user"])
@limiter.limit("10/minute")
async def login_with_sakey(request: Request, credentials: dict = Body(...)):
    client_id = credentials.get("client_id")
    private_key = credentials.get("private_key")

    if not client_id or not private_key:
        raise HTTPException(status_code=400, detail=random.choice(usrnotallowed))

    sa_user = await usrcollection.find_one(
        {"client_id": client_id, "type": "sa", "is_active": True}
    )
    if not sa_user:
        raise HTTPException(status_code=401, detail=random.choice(usrnotallowed))

    if not Hasher.verify_password(private_key, sa_user["private_key"]):
        raise HTTPException(status_code=401, detail=random.choice(usrnotallowed))

    access_token = create_jwt_token_sakey(
        {
            "client_id": sa_user["client_id"],
            "cln": sa_user["client_id"],
            "lvl": sa_user["group_access"],
            "sts": sa_user["is_active"],
            "tim": sa_user["data_domain"],
            "typ": sa_user["type"],
        },
        sa_exp * 24 * 60,  # convert days to minutes
    )

    expire_at = datetime.utcnow() + timedelta(days=sa_exp)
    response = JSONResponse(
        content={
            "message": "Login successful (SAKey)",
            "client_id": sa_user["client_id"],
            "expire_at": expire_at.isoformat() + "Z",
        }
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="Strict",
    )
    return response


@app.post("/logout")
async def logout_user():
    response = JSONResponse(content={"message": "Logout successful"})
    response.delete_cookie("access_token", path="/")
    return response


# # # ======================= Users
# # # ======================= Bagian ini untuk kebutuhan manajemen user
@app.post("/user/create", tags=["user"])
async def create_user(
    user_form: UserCreate, current_user: dict = Depends(token_verification)
):
    # # checking access level
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvladmin)
    # # checking access level

    if not user_form.username:
        raise HTTPException(status_code=412, detail=usr_412_uname)
    if not user_form.password:
        raise HTTPException(status_code=412, detail=usr_412_pwd)
    if not user_form.name:
        raise HTTPException(status_code=412, detail=usr_412_name)
    if not user_form.group_access:
        raise HTTPException(status_code=412, detail=usr_412_level)
    if not user_form.data_domain:
        raise HTTPException(status_code=412, detail=usr_412_team)
    # if not user_form.is_active:
    #     raise HTTPException(status_code=412, detail="Status active is required")

    user_info = await usrcollection.find_one({"username": user_form.username})

    # Cek apakah user yang digunakan adalah root
    # karena hanya root yang boleh menambahkan user root lainya
    if user_level not in grplvlroot or user_status == False:
        raise HTTPException(status_code=403, detail=random.choice(usrnotallowed))

    # Cek apakah sudah ada user root active
    # itupun dalam kondisi root yang ditambahkan harus mode is_active = False
    if user_form.group_access in grplvlroot and user_form.is_active == True:
        raise HTTPException(status_code=409, detail=usr_409_root)

    # Cek apakah username sudah ada
    if user_info:
        raise HTTPException(status_code=409, detail=usr_409_taken)

    # Cek apakah password terdiri dari minimal 8 char
    if len(user_form.password) < 8:
        raise HTTPException(status_code=422, detail=pwd_422_long)

    # Cek apakah password terdiri dari huruf besar, kecil, angka serta char khusus
    valid_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+={}[]<>,./?;:'\""
    )
    if not any(c in valid_chars for c in user_form.password):
        raise HTTPException(status_code=422, detail=pwd_422_all)

    # Cek apakah password mengandung setidaknya satu huruf besar, satu huruf kecil, satu angka, dan satu karakter khusus
    if not any(c.isupper() for c in user_form.password):
        raise HTTPException(status_code=422, detail=pwd_422_upcase)

    if not any(c.islower() for c in user_form.password):
        raise HTTPException(status_code=422, detail=pwd_422_locase)

    if not any(c.isdigit() for c in user_form.password):
        raise HTTPException(status_code=422, detail=pwd_422_num)

    if not any(c in valid_chars for c in user_form.password if not c.isalnum()):
        raise HTTPException(status_code=422, detail=pwd_422_spc)

    # data_domain harus terdaftar di katalog domain (jika katalog sudah dipakai)
    await validate_data_domain(user_form.data_domain)

    # hashing password
    hashed_password = Hasher.get_password_hash(user_form.password)

    # populate user data
    user_data = {
        "username": user_form.username,
        "password": hashed_password,
        "name": user_form.name,
        "group_access": user_form.group_access,
        "data_domain": user_form.data_domain,
        "is_active": user_form.is_active,
        "type": "user",
        "created_at": current_dateTime,
    }

    # insert user
    await usrcollection.insert_one(user_data)

    return {"message": "User created successfully"}


@app.get("/sakey/create", tags=["user"])
async def create_sakey(current_user: dict = Depends(token_verification)):
    if current_user.get("typ") != "user":
        raise HTTPException(status_code=403, detail=random.choice(botnotallowed))

    # # checking access level
    user_uname = current_user["usr"]
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    user_team = current_user["tim"]
    await access_verification(user_level, user_status, grplvldev)
    # # checking access level

    if user_level not in grplvldev or user_status == False:
        raise HTTPException(status_code=403, detail=random.choice(usrnotallowed))

    clientid = cn_generator()

    user_data = {
        "cln": clientid,
        "usr": user_uname,
        "typ": "sa",
        "lvl": user_level,
        "sts": user_status,
        "tim": user_team,
    }

    privatekey = create_private_key(user_data, sa_exp)
    hashed_privatekey = Hasher.get_password_hash(privatekey)
    expire_at = datetime.utcnow() + timedelta(days=sa_exp)

    sa_data = {
        "client_id": clientid,
        "private_key": hashed_privatekey,
        "type": "sa",
        "generated_by": user_uname,
        "generated_at": current_dateTime,
        "group_access": user_level,
        "data_domain": user_team,
        "is_active": True,
        "expire_at": expire_at,
        "created_at": current_dateTime,
    }

    # insert user
    await usrcollection.insert_one(sa_data)

    return {
        "client_id": clientid,
        "private_key": privatekey,
        "generated_by": user_uname,
        "generated_at": current_dateTime,
    }


@app.get("/sakey/lists", tags=["user"])
async def list_sakeys(current_user: dict = Depends(token_verification)):
    if current_user.get("typ") != "user":
        raise HTTPException(status_code=403, detail=random.choice(botnotallowed))

    user_uname = current_user.get("usr")
    user_level = current_user.get("lvl")
    user_status = current_user.get("sts")

    await access_verification(user_level, user_status, grplvlall)

    # Jika user adalah root, tampilkan semua SAKey
    if user_level in grplvlroot:
        sakey_cursor = usrcollection.find({"type": "sa"})
    else:
        # Jika bukan root, hanya tampilkan SAKey yang dibuat oleh user sendiri
        sakey_cursor = usrcollection.find({"type": "sa", "generated_by": user_uname})

    sakey_list = []
    async for sakey in sakey_cursor:
        sakey_list.append(
            {
                "client_id": sakey.get("client_id"),
                "generated_at": sakey.get("generated_at"),
                "is_active": current_user.get("sts"),
                "expire_at": sakey.get("expire_at"),
            }
        )

    return {"sakeys": sakey_list}


@app.get("/user/lists", tags=["user"])
async def list_users(current_user: dict = Depends(require_admin)):
    """List semua user. Hanya dapat diakses oleh root dan admin."""
    cursor = usrcollection.find({}, {"_id": 0, "password": 0, "private_key": 0})
    users = await cursor.to_list(length=500)
    return users


@app.get("/user/basic", tags=["user"])
async def list_users_basic(current_user: dict = Depends(require_any)):
    """Direktori ringan {username, name} user **aktif** untuk pengisian
    stakeholder kontrak. Hanya field yang diperlukan UI di-expose, sehingga
    bisa dibuka ke semua role tanpa kebocoran data sensitif.
    """
    cursor = usrcollection.find(
        {"is_active": True, "type": {"$ne": "sa"}},
        {"_id": 0, "username": 1, "name": 1},
    )
    return await cursor.to_list(length=500)


@app.patch("/user/{username}", tags=["user"])
async def update_user(username: str, payload: dict = Body(...), current_user: dict = Depends(require_root)):
    """Edit user (nama, peran, domain, status aktif, password). Hanya root."""
    target = await usrcollection.find_one({"username": username})
    if not target or target.get("type") == "sa":
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")

    # Tidak boleh edit sesama root
    if target.get("group_access") in grplvlroot:
        raise HTTPException(status_code=403, detail="Tidak dapat mengubah akun root lain.")

    allowed_fields = {"name", "group_access", "data_domain", "is_active", "password"}
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}

    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada field yang valid untuk diupdate.")

    if "password" in update_data:
        pwd = update_data["password"]
        if len(pwd) < 8 or not any(c.isupper() for c in pwd) or not any(c.islower() for c in pwd) \
                or not any(c.isdigit() for c in pwd) or not any(not c.isalnum() for c in pwd):
            raise HTTPException(status_code=422, detail="Password harus min. 8 karakter, mengandung huruf besar, kecil, angka, dan karakter khusus.")
        update_data["password"] = Hasher.get_password_hash(pwd)

    if "group_access" in update_data and update_data["group_access"] in grplvlroot:
        raise HTTPException(status_code=403, detail="Tidak dapat mengubah peran menjadi root.")

    if "data_domain" in update_data:
        await validate_data_domain(update_data["data_domain"])

    await usrcollection.update_one({"username": username}, {"$set": update_data})
    return {"message": f"User '{username}' berhasil diperbarui."}


@app.delete("/user/{username}", tags=["user"])
async def delete_user(username: str, current_user: dict = Depends(require_root)):
    """Hapus user permanen. Hanya root. Tidak bisa hapus root lain."""
    target = await usrcollection.find_one({"username": username})
    if not target or target.get("type") == "sa":
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")

    if target.get("group_access") in grplvlroot:
        raise HTTPException(status_code=403, detail="Tidak dapat menghapus akun root.")

    caller = current_user["usr"]
    if username == caller:
        raise HTTPException(status_code=403, detail="Tidak dapat menghapus akun sendiri.")

    await usrcollection.delete_one({"username": username})
    return {"message": f"User '{username}' berhasil dihapus."}


# ── Domain management ─────────────────────────────────────────────────────────
# `data_domain` adalah kunci akses kontrak (exact-string match di
# /datacontract/filter). Katalog domain terstandarisasi mencegah typo /
# inkonsistensi kapitalisasi yang membuat user kehilangan akses. Lihat #34.


@app.get("/domain/lists", tags=["domain"])
async def list_domains(
    include_inactive: bool = False,
    current_user: dict = Depends(require_admin),
):
    """Daftar domain. Default hanya domain aktif — `include_inactive=true`
    untuk menyertakan domain yang sudah dinonaktifkan (halaman manajemen)."""
    query = {} if include_inactive else {"is_active": True}
    cursor = domcollection.find(query, {"_id": 0})
    domains = await cursor.to_list(length=500)
    for d in domains:
        d["user_count"] = await usrcollection.count_documents(
            {"data_domain": d["name"], "type": "user"}
        )
    domains.sort(key=lambda d: (d.get("label") or d.get("name") or "").lower())
    return domains


@app.get("/domain/basic", tags=["domain"])
async def list_domains_basic(current_user: dict = Depends(require_any)):
    """Direktori ringan {name, label} domain **aktif** untuk pengisian
    field Pemilik kontrak (#73). Mirror pola /user/basic — minim data,
    bisa diakses semua role tanpa kebocoran info sensitif."""
    cursor = domcollection.find(
        {"is_active": True},
        {"_id": 0, "name": 1, "label": 1},
    )
    domains = await cursor.to_list(length=500)
    domains.sort(key=lambda d: (d.get("label") or d.get("name") or "").lower())
    return domains


@app.post("/domain/create", tags=["domain"], status_code=201)
async def create_domain(
    payload: DomainCreate, current_user: dict = Depends(require_admin)
):
    """Buat domain baru. `name` di-slugify jadi kunci matching lowercase."""
    name = slugify_domain(payload.name)
    if not name:
        raise HTTPException(status_code=412, detail="Nama domain wajib diisi.")
    label = (payload.label or "").strip()
    if not label:
        raise HTTPException(status_code=412, detail="Label domain wajib diisi.")
    if await domcollection.find_one({"name": name}):
        raise HTTPException(status_code=409, detail=f"Domain '{name}' sudah ada.")
    await domcollection.insert_one({
        "name": name,
        "label": label,
        "description": (payload.description or "").strip(),
        "is_active": True,
        "created_at": datetime.now(),
    })
    return {"message": f"Domain '{label}' berhasil dibuat.", "name": name}


@app.patch("/domain/{name}", tags=["domain"])
async def update_domain(
    name: str, payload: DomainUpdate, current_user: dict = Depends(require_admin)
):
    """Edit label / deskripsi / status aktif. `name` tidak bisa diubah."""
    target = await domcollection.find_one({"name": name})
    if not target:
        raise HTTPException(status_code=404, detail="Domain tidak ditemukan.")

    # Domain default ('root', 'admin') read-only sepenuhnya (#85).
    # Why: rename label `admin` → "Root" akan bentrok dengan label domain `root`
    # di dropdown user assignment dan membuka jalan social engineering.
    if target.get("is_default"):
        raise HTTPException(
            status_code=409,
            detail=f"Domain default '{name}' tidak bisa diubah.",
        )

    update_data: dict = {}
    if payload.label is not None:
        label = payload.label.strip()
        if not label:
            raise HTTPException(status_code=412, detail="Label domain wajib diisi.")
        update_data["label"] = label
    if payload.description is not None:
        update_data["description"] = payload.description.strip()
    if payload.is_active is not None:
        update_data["is_active"] = payload.is_active

    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada field yang valid untuk diupdate.")

    await domcollection.update_one({"name": name}, {"$set": update_data})
    return {"message": f"Domain '{name}' berhasil diperbarui."}


@app.delete("/domain/{name}", tags=["domain"])
async def deactivate_domain(
    name: str, current_user: dict = Depends(require_admin)
):
    """Nonaktifkan domain (soft delete). Dokumen tetap disimpan karena
    user existing mungkin masih memakai domain ini sebagai `data_domain`."""
    target = await domcollection.find_one({"name": name})
    if not target:
        raise HTTPException(status_code=404, detail="Domain tidak ditemukan.")
    # Domain default ('root', 'admin') tidak boleh dihapus (#74).
    if target.get("is_default"):
        raise HTTPException(
            status_code=409,
            detail=f"Domain default '{name}' tidak bisa dihapus.",
        )
    await domcollection.update_one({"name": name}, {"$set": {"is_active": False}})
    return {"message": f"Domain '{name}' dinonaktifkan."}


# Example route to get user data
@app.get("/user/me", response_model=dict, tags=["user"])
async def who_am_i(current_user: dict = Depends(token_verification)):
    if current_user.get("typ") != "user":
        raise HTTPException(status_code=403, detail=random.choice(botnotallowed))

    return {
        "client_id": current_user.get("usr"),
        "group_access": current_user.get("lvl"),
        "data_domain": current_user.get("tim"),
        "is_active": current_user.get("sts"),
        "type": current_user.get("typ"),
    }


# Example route to get user data
@app.get("/sakey/me", response_model=dict, tags=["user"])
async def sakey_info(current_user: dict = Depends(token_verification)):
    if current_user.get("typ") != "sa":
        raise HTTPException(status_code=403, detail=random.choice(hmnnotallowed))

    return {
        "client_id": current_user.get("client_id") or current_user.get("cln"),
        "group_access": current_user.get("lvl"),
        "data_domain": current_user.get("tim"),
        "is_active": current_user.get("sts"),
        "type": current_user.get("typ"),
    }


# # # ======================= Data Contract
# # # ======================= Bagian ini untuk kebutuhan menampilkan Data Contract tanpa filter
@app.get("/datacontract/gencn", tags=["datacontract"])
async def generate_contract_number(current_user: dict = Depends(token_verification)):
    # # checking access level
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    user_uname = current_user["usr"]
    await access_verification(user_level, user_status, grplvlall)
    # # checking access level

    code = cn_generator()

    return {
        "contract_number": code,
        "generated_by": user_uname,
        "generated_at": current_dateTime,
    }


@app.post("/datacontract/add", tags=["datacontract"])
async def insert_datacontract(
    data: All, current_user: dict = Depends(token_verification)
):
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvlall)

    payload = data.dict()
    payload["created_by"] = current_user["usr"]
    payload["managers"] = []
    payload["approval_status"] = None
    payload["pending_changes"] = None
    payload["pending_by"] = None

    existing = await dccollection.find_one(
        {"contract_number": payload["contract_number"]},
        {"_id": 1},
    )
    if existing:
        raise HTTPException(status_code=409, detail=dc_409)

    try:
        await dccollection.insert_one(payload)
        return {"message": "Insert Success"}
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail=dc_409)


@app.put("/datacontract/update", tags=["datacontract"])
async def update_datacontract(
    contract_number: str, data: All, current_user: dict = Depends(token_verification)
):
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    username = current_user["usr"]
    await access_verification(user_level, user_status, grplvlall)

    existing = await dccollection.find_one({"contract_number": contract_number})
    if not existing:
        raise HTTPException(status_code=404, detail=dcnotfound)

    # developer/user: hanya bisa edit kontrak milik sendiri
    if user_level not in grplvladmin:
        is_owner = existing.get("created_by") == username
        is_manager = username in (existing.get("managers") or [])
        if not is_owner and not is_manager:
            raise HTTPException(status_code=403, detail=random.choice(usrnotallowed))

    try:
        payload = data.dict()
        payload.pop("contract_number", None)

        if user_level in grplvladmin:
            # admin/root: langsung terapkan perubahan
            await dccollection.update_one(
                {"contract_number": contract_number},
                {"$set": payload}
            )
            return {"message": "Update Success"}
        else:
            # developer/user: simpan sebagai pending + buat approval record
            # ADR-0004: approver diturunkan per peran (steward + producer + consumer)
            # Sumber payload dipakai supaya stakeholder yang baru ditambahkan langsung
            # ikut menjadi approver — bukan dari `existing` yang masih state lama.
            contract_for_derivation = {"metadata": payload.get("metadata") or {}}
            approvers_by_role, fallback_roles = await derive_approvers_by_role(
                contract_for_derivation
            )
            approvers = sorted({u for users in approvers_by_role.values() for u in users})

            from nanoid import generate
            approval_id = generate(size=16)

            approval_doc = {
                "approval_id": approval_id,
                "contract_number": contract_number,
                "requested_by": username,
                "proposed_changes": payload,
                "approvers": approvers,
                "approvers_by_role": approvers_by_role,
                "fallback_roles": fallback_roles,
                "votes": [],
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "resolved_at": None,
            }
            await aprcollection.insert_one(approval_doc)

            await dccollection.update_one(
                {"contract_number": contract_number},
                {"$set": {
                    "approval_status": "pending",
                    "pending_changes": payload,
                    "pending_by": username,
                    "approval_id": approval_id,
                }}
            )
            return {
                "message": "Perubahan diajukan dan menunggu persetujuan pengelola kontrak.",
                "approval_id": approval_id,
                "approvers": approvers,
            }
    except Exception as e:
        return {"error": str(e)}


@app.get("/datacontract/lists", tags=["datacontract"])
async def get_datacontract(current_user: dict = Depends(token_verification)):
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    username = current_user["usr"]
    await access_verification(user_level, user_status, grplvlall)

    if user_level in grplvladmin:
        # admin/root: lihat semua kontrak
        docs = await dccollection.find({}, {"_id": 0}).to_list(None)
    else:
        # developer/user: hanya kontrak yang dibuat atau ditugaskan
        docs = await dccollection.find(
            {"$or": [{"created_by": username}, {"managers": username}]},
            {"_id": 0}
        ).to_list(None)

    return [All(**doc) for doc in docs] if docs else []


@app.get("/datacontract/mine", tags=["datacontract"])
async def get_my_contracts(current_user: dict = Depends(token_verification)):
    """Kontrak yang dibuat atau ditugaskan kepada user yang sedang login."""
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    username = current_user["usr"]
    await access_verification(user_level, user_status, grplvlall)

    docs = await dccollection.find(
        {"$or": [{"created_by": username}, {"managers": username}]},
        {"_id": 0}
    ).to_list(None)

    return [All(**doc) for doc in docs] if docs else []


@app.get("/datacontract/metadata", tags=["datacontract"])
async def get_datacontract_metadata(current_user: dict = Depends(token_verification)):
    # # checking access level
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvladmin)
    # # checking access level

    dclist = await display_metadata()

    return dclist


@app.get("/datacontract/model", tags=["datacontract"])
async def get_datacontract_model(current_user: dict = Depends(token_verification)):
    # # checking access level
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvladmin)
    # # checking access level

    dclist = await display_model()

    return dclist


@app.get("/datacontract/ports", tags=["datacontract"])
async def get_datacontract_ports(current_user: dict = Depends(token_verification)):
    # # checking access level
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvladmin)
    # # checking access level

    dclist = await display_ports()

    return dclist


@app.get("/datacontract/examples", tags=["datacontract"])
async def get_datacontract_examples(current_user: dict = Depends(token_verification)):
    # # checking access level
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvladmin)
    # # checking access level

    dclist = await display_examples()

    return dclist


# # # ======================= Data Contract filtered
# # # ======================= Bagian ini untuk kebutuhan menampilkan Data Contract berdasarkan filter contract_number
@app.get("/datacontract/filter", tags=["datacontract_filtered"])
async def get_datacontract_filter(
    contract_number: str = None, current_user: dict = Depends(token_verification)
):
    user_client = current_user.get("cln")
    user_uname = current_user.get("usr")
    user_level = current_user.get("lvl")
    user_status = current_user.get("sts")
    user_team = current_user.get("tim")

    if contract_number:
        # Specific contract — full access check including consumer validation
        await access_verification_filter(
            user_uname, user_level, user_status, grplvlall,
            user_team, user_client, contract_number,
        )
        dcfilter = await display_all(contract_number)
        return dcfilter
    else:
        # List mode — return all contracts accessible to this user
        await access_verification(user_level, user_status, grplvlall)
        if user_level in grplvladmin:
            dcfilter = await display_all()
        else:
            # Filter contracts where user's team is listed as consumer
            all_contracts = await dccollection.find().to_list(None)
            accessible = [
                c for c in all_contracts
                if user_team in [
                    m.get("name") for m in (c.get("metadata") or {}).get("consumer") or []
                ]
            ]
            if not accessible:
                return []
            from app.model.all import All as AllModel
            dcfilter = [AllModel(**c) for c in accessible]
        return dcfilter


@app.get("/datacontract/metadata/filter", tags=["datacontract_filtered"])
async def get_datacontract_metadata_filter(
    contract_number: str = None, current_user: dict = Depends(token_verification)
):
    # # checking access level
    user_client = current_user.get("cln")
    user_uname = current_user.get("usr")
    user_level = current_user.get("lvl")
    user_status = current_user.get("sts")
    user_team = current_user.get("tim")
    await access_verification_filter(
        user_uname,
        user_level,
        user_status,
        grplvlall,
        user_team,
        user_client,
        contract_number,
    )
    # # checking access level

    dcfilter = await display_metadata(contract_number)

    return dcfilter


@app.get("/datacontract/model/filter", tags=["datacontract_filtered"])
async def get_datacontract_model_filter(
    contract_number: str = None, current_user: dict = Depends(token_verification)
):
    # # checking access level
    user_client = current_user.get("cln")
    user_uname = current_user.get("usr")
    user_level = current_user.get("lvl")
    user_status = current_user.get("sts")
    user_team = current_user.get("tim")
    await access_verification_filter(
        user_uname,
        user_level,
        user_status,
        grplvlall,
        user_team,
        user_client,
        contract_number,
    )
    # # checking access level

    dcfilter = await display_model(contract_number)

    return dcfilter


@app.get("/datacontract/ports/filter", tags=["datacontract_filtered"])
async def get_datacontract_ports_filter(
    contract_number: str = None, current_user: dict = Depends(token_verification)
):
    # # checking access level
    user_client = current_user.get("cln")
    user_uname = current_user.get("usr")
    user_level = current_user.get("lvl")
    user_status = current_user.get("sts")
    user_team = current_user.get("tim")
    await access_verification_filter(
        user_uname,
        user_level,
        user_status,
        grplvlall,
        user_team,
        user_client,
        contract_number,
    )
    # # checking access level

    dcfilter = await display_ports(contract_number)

    return dcfilter


@app.get("/datacontract/examples/filter", tags=["datacontract_filtered"])
async def get_datacontract_examples_filter(
    contract_number: str = None, current_user: dict = Depends(token_verification)
):
    # # checking access level
    user_client = current_user.get("cln")
    user_uname = current_user.get("usr")
    user_level = current_user.get("lvl")
    user_status = current_user.get("sts")
    user_team = current_user.get("tim")
    await access_verification_filter(
        user_uname,
        user_level,
        user_status,
        grplvlall,
        user_team,
        user_client,
        contract_number,
    )
    # # checking access level

    dcfilter = await display_examples(contract_number)

    return dcfilter


@app.get("/datacontract/dbtschema/filter", tags=["datacontract_filtered"])
async def get_datacontract_dbtschema_filter(
    contract_number: str = None, current_user: dict = Depends(token_verification)
):
    # # checking access level
    user_client = current_user.get("cln")
    user_uname = current_user.get("usr")
    user_level = current_user.get("lvl")
    user_status = current_user.get("sts")
    user_team = current_user.get("tim")
    await access_verification_filter(
        user_uname,
        user_level,
        user_status,
        grplvlall,
        user_team,
        user_client,
        contract_number,
    )
    # # checking access level

    dcfilter = await display_dbtschema(contract_number)

    return dcfilter


# # # ======================= Rule Catalog
# # # ======================= Bagian ini untuk manajemen katalog aturan kualitas

@app.post("/catalog/seed", tags=["catalog"], include_in_schema=False)
async def seed_builtin_rules(user=Depends(require_root)):
    """Isi katalog dengan modul bawaan. Hanya bisa dipanggil oleh root."""
    existing = await catalogcollection.count_documents({})
    if existing > 0:
        raise HTTPException(status_code=409, detail="Katalog sudah memiliki data.")
    catalog_rules = load_catalog_rules_addon()
    await catalogcollection.insert_many(catalog_rules)
    return {"message": f"{len(catalog_rules)} modul bawaan berhasil ditambahkan."}


@app.get("/catalog/rules", tags=["catalog"])
async def get_all_rules(user=Depends(require_any)):
    """
    Ambil semua modul aturan kualitas.
    Semua role bisa mengakses (read-only untuk developer & user).
    """
    cursor = catalogcollection.find({}, {"_id": 0})
    rules = await cursor.to_list(length=200)
    return rules


@app.get("/catalog/rules/{code}", tags=["catalog"])
async def get_rule_by_code(code: str, user=Depends(require_any)):
    """Ambil detail satu modul berdasarkan code."""
    rule = await catalogcollection.find_one({"code": code}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail=f"Modul '{code}' tidak ditemukan.")
    return rule


@app.post("/catalog/rules", tags=["catalog"], status_code=201)
async def create_rule(payload: RuleCatalogCreate, user=Depends(require_any)):
    """
    Tambah modul aturan baru ke katalog.

    - Admin/root → langsung disimpan ke katalog.
    - User/developer → masuk approval workflow, menunggu persetujuan
      steward (admin/root) sebelum benar-benar tersimpan (issue #69).

    Code unik diperiksa di kedua jalur untuk mencegah konflik nama saat
    submit (tetap mungkin terjadi race condition di antara submit & approve;
    bila konflik baru terlihat saat apply, vote handler menolak).
    """
    username = user["usr"]
    user_level = user["lvl"]

    existing = await catalogcollection.find_one({"code": payload.code})
    if existing:
        raise HTTPException(status_code=409, detail=f"Modul dengan code '{payload.code}' sudah ada.")

    doc = payload.model_dump()
    doc["is_builtin"] = False
    doc["is_active"] = True

    # Admin/root: commit langsung — perilaku lama.
    if user_level in grplvladmin:
        await catalogcollection.insert_one(doc)
        created = await catalogcollection.find_one({"code": payload.code}, {"_id": 0})
        return created

    # User/developer: jalur approval. Cegah duplikasi pengajuan aktif
    # untuk code yang sama supaya tidak ada dua approval saling overwrite
    # di saat di-apply.
    pending_dup = await aprcollection.find_one({
        "type": "rule_catalog_create",
        "target_id": payload.code,
        "status": "pending",
    })
    if pending_dup:
        raise HTTPException(
            status_code=409,
            detail=f"Pengajuan modul '{payload.code}' sudah ada dan menunggu persetujuan.",
        )

    approvers_by_role, fallback_roles = await derive_catalog_approvers()
    approvers = sorted({u for users in approvers_by_role.values() for u in users})
    if not approvers:
        # Tidak ada steward aktif → tidak ada yang bisa menyetujui.
        raise HTTPException(
            status_code=503,
            detail="Tidak ada steward (admin/root) aktif untuk menyetujui pengajuan. "
                   "Hubungi administrator sistem.",
        )

    from nanoid import generate
    approval_id = generate(size=16)

    approval_doc = {
        "approval_id":       approval_id,
        "type":              "rule_catalog_create",
        "target_id":         payload.code,
        "requested_by":      username,
        "proposed_changes":  doc,
        "approvers":         approvers,
        "approvers_by_role": approvers_by_role,
        "fallback_roles":    fallback_roles,
        "votes":             [],
        "status":            "pending",
        "created_at":        datetime.now().isoformat(),
        "resolved_at":       None,
    }
    await aprcollection.insert_one(approval_doc)

    return {
        "message":     "Modul aturan diajukan dan menunggu persetujuan steward.",
        "approval_id": approval_id,
        "approvers":   approvers,
        "rule_code":   payload.code,
        "status":      "pending",
    }


@app.patch("/catalog/rules/{code}", tags=["catalog"])
async def update_rule(code: str, payload: RuleCatalogUpdate, user=Depends(require_admin)):
    """
    Update modul kustom. Modul bawaan (is_builtin=True) tidak bisa diubah.
    Hanya root dan admin.
    """
    rule = await catalogcollection.find_one({"code": code})
    if not rule:
        raise HTTPException(status_code=404, detail=f"Modul '{code}' tidak ditemukan.")
    if rule.get("is_builtin"):
        raise HTTPException(status_code=403, detail="Modul bawaan tidak bisa diubah.")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    await catalogcollection.update_one({"code": code}, {"$set": update_data})
    updated = await catalogcollection.find_one({"code": code}, {"_id": 0})
    return updated


@app.delete("/catalog/rules/{code}", tags=["catalog"])
async def delete_rule(code: str, user=Depends(require_admin)):
    """
    Hapus modul kustom. Modul bawaan tidak bisa dihapus.
    Hanya root dan admin.
    """
    rule = await catalogcollection.find_one({"code": code})
    if not rule:
        raise HTTPException(status_code=404, detail=f"Modul '{code}' tidak ditemukan.")
    if rule.get("is_builtin"):
        raise HTTPException(status_code=403, detail="Modul bawaan tidak bisa dihapus.")

    await catalogcollection.delete_one({"code": code})
    return {"message": f"Modul '{code}' berhasil dihapus."}


# # # ======================= YAML Import & Validation
# # # ======================= Bagian ini untuk validasi dan import file YAML

@app.post("/contracts/validate-yaml", tags=["contracts"])
async def validate_yaml_import(
    file: UploadFile = File(...),
    user=Depends(require_admin),
):
    """
    Validasi file YAML data contract sebelum diimport.
    Hanya root dan admin.
    """
    content = await file.read()

    # ── Layer 1: YAML syntax
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return {
            "valid": False,
            "layer": "yaml_syntax",
            "errors": [{"line": getattr(e, "problem_mark", None) and e.problem_mark.line + 1,
                        "message": str(e)}],
            "suggestions": ["Periksa indentasi YAML — gunakan spasi, bukan tab.",
                            "Pastikan setiap key diikuti tanda titik dua dan spasi: 'key: value'"],
        }

    if not isinstance(data, dict):
        return {"valid": False, "layer": "yaml_syntax",
                "errors": [{"message": "File YAML harus berupa objek/mapping di level teratas."}],
                "suggestions": []}

    # ── Layer 2: ODCS schema
    errors = []
    warnings = []

    for field in ["standard_version", "metadata"]:
        if field not in data:
            errors.append({"field": field, "message": f"Field wajib '{field}' tidak ditemukan."})

    metadata = data.get("metadata", {})
    if isinstance(metadata, dict):
        for mf in ["name", "owner", "version", "type"]:
            if not metadata.get(mf):
                errors.append({"field": f"metadata.{mf}",
                                "message": f"Field wajib 'metadata.{mf}' tidak ditemukan atau kosong."})

        if not data.get("contract_number"):
            warnings.append({"field": "contract_number",
                             "message": "contract_number tidak ada — akan digenerate otomatis oleh sistem."})

        valid_roles = {"owner","consumer","steward","producer","engineer","analyst","architect"}
        for i, s in enumerate(metadata.get("stakeholders") or []):
            if s.get("role") and s["role"] not in valid_roles:
                errors.append({
                    "field": f"metadata.stakeholders[{i}].role",
                    "message": f"Nilai role '{s['role']}' tidak valid.",
                    "suggestion": f"Ganti dengan salah satu: {', '.join(sorted(valid_roles))}",
                })

        sla = metadata.get("sla") or {}
        if "retention" in sla and not isinstance(sla["retention"], int):
            errors.append({
                "field": "metadata.sla.retention",
                "message": f"'retention' harus berupa angka bulat (integer), ditemukan: {type(sla['retention']).__name__}",
                "suggestion": "Ubah nilai retention menjadi angka: retention: 1 (bukan '1 tahun').",
            })

        valid_dims = {"completeness", "validity", "accuracy", "security"}
        for i, q in enumerate(metadata.get("quality") or []):
            if q.get("dimension") and q["dimension"] not in valid_dims:
                errors.append({
                    "field": f"metadata.quality[{i}].dimension",
                    "message": f"Dimensi '{q['dimension']}' tidak valid.",
                    "suggestion": f"Gunakan salah satu: {', '.join(sorted(valid_dims))}",
                })

    for i, col in enumerate(data.get("model") or []):
        if not col.get("column"):
            errors.append({"field": f"model[{i}].column",
                           "message": "Nama kolom tidak boleh kosong."})
        for j, q in enumerate(col.get("quality") or []):
            if not q.get("dimension"):
                errors.append({
                    "field": f"model[{i}].quality[{j}].dimension",
                    "message": "Field 'dimension' wajib ada di setiap aturan kualitas kolom.",
                })

    if errors:
        return {
            "valid": False,
            "layer": "odcs_schema",
            "errors": errors,
            "warnings": warnings,
            "suggestions": [e.get("suggestion") for e in errors if e.get("suggestion")],
        }

    summary = {
        "contract_name": metadata.get("name"),
        "owner": metadata.get("owner"),
        "type": metadata.get("type"),
        "version": metadata.get("version"),
        "columns": len(data.get("model") or []),
        "dataset_quality_rules": len(metadata.get("quality") or []),
        "column_quality_rules": sum(len(c.get("quality") or []) for c in (data.get("model") or [])),
        "stakeholders": len(metadata.get("stakeholders") or []),
        "has_contract_number": bool(data.get("contract_number")),
        "raw": data,
    }

    return {
        "valid": True,
        "layer": "passed",
        "warnings": warnings,
        "summary": summary,
    }


@app.post("/contracts/import-yaml", tags=["contracts"], status_code=201)
async def import_yaml_contract(
    file: UploadFile = File(...),
    user=Depends(require_admin),
):
    """
    Import data contract dari file YAML.
    Hanya root dan admin.
    """
    content = await file.read()

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=422, detail=f"YAML syntax error: {str(e)}")

    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="File YAML tidak valid.")

    if not data.get("contract_number"):
        data["contract_number"] = await cn_generator()

    existing = await dccollection.find_one({"contract_number": data["contract_number"]})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Kontrak dengan nomor '{data['contract_number']}' sudah ada."
        )

    await dccollection.insert_one(data)
    saved = await dccollection.find_one(
        {"contract_number": data["contract_number"]}, {"_id": 0}
    )
    return saved


# # # ======================= Approval Endpoints =======================

@app.get("/approval/pending", tags=["approval"])
async def get_pending_approvals(current_user: dict = Depends(token_verification)):
    """Daftar approval yang menunggu vote dari user yang sedang login."""
    username = current_user["usr"]
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvlall)

    docs = await aprcollection.find(
        {"approvers": username, "status": "pending", "votes.username": {"$ne": username}},
        {"_id": 0}
    ).to_list(None)
    return docs


@app.get("/approval/mine", tags=["approval"])
async def get_my_approvals(current_user: dict = Depends(token_verification)):
    """Daftar approval yang diajukan oleh user yang sedang login."""
    username = current_user["usr"]
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvlall)

    docs = await aprcollection.find(
        {"requested_by": username},
        {"_id": 0}
    ).to_list(None)
    return docs


@app.post("/approval/{approval_id}/vote", tags=["approval"])
async def vote_approval(
    approval_id: str,
    vote_data: VoteRequest,
    current_user: dict = Depends(token_verification),
):
    """Cast approve/reject vote. Jika semua setuju → terapkan perubahan."""
    username = current_user["usr"]
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvlall)

    record = await aprcollection.find_one({"approval_id": approval_id})
    if not record:
        raise HTTPException(status_code=404, detail="Approval tidak ditemukan.")
    if record["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Approval sudah {record['status']}.")
    if username not in record["approvers"]:
        raise HTTPException(status_code=403, detail=random.choice(usrnotallowed))
    already_voted = any(v["username"] == username for v in record.get("votes", []))
    if already_voted:
        raise HTTPException(status_code=409, detail="Anda sudah memberikan vote.")

    new_vote = {
        "username": username,
        "vote": vote_data.vote,
        "reason": vote_data.reason,
        "voted_at": datetime.now().isoformat(),
    }
    await aprcollection.update_one({"approval_id": approval_id}, {"$push": {"votes": new_vote}})

    # Tipe pengajuan — default contract_change untuk approval lama (issue #69).
    approval_type = record.get("type", "contract_change")

    if vote_data.vote == "rejected":
        await aprcollection.update_one(
            {"approval_id": approval_id},
            {"$set": {"status": "rejected", "resolved_at": datetime.now().isoformat()}},
        )
        # Reset state pending hanya untuk perubahan kontrak. Untuk rule
        # catalog, tidak ada side-effect lain yang perlu di-rollback.
        if approval_type == "contract_change":
            await dccollection.update_one(
                {"contract_number": record.get("contract_number")},
                {"$set": {"approval_status": "rejected", "pending_changes": None, "pending_by": None, "approval_id": None}},
            )
        return {"message": "Pengajuan ditolak."}

    updated = await aprcollection.find_one({"approval_id": approval_id})
    # ADR-0004/0005: konsensus berbasis peran untuk approval baru;
    # fallback ke logika lama (unanimous count) untuk approval in-flight
    # yang dibuat sebelum migrasi.
    approvers_by_role = updated.get("approvers_by_role")
    if approvers_by_role:
        consensus = is_consensus_reached(approvers_by_role, updated["votes"])
    else:
        approved_votes = [v for v in updated["votes"] if v["vote"] == "approved"]
        consensus = len(approved_votes) == len(record["approvers"])

    if not consensus:
        return {"message": "Vote diterima. Menunggu persetujuan anggota lain."}

    # Konsensus tercapai → terapkan sesuai jenis pengajuan.
    if approval_type == "contract_change":
        _allowed = {"standard_version", "metadata", "model", "ports", "examples"}
        changes = {k: v for k, v in record["proposed_changes"].items() if k in _allowed}
        changes["approval_status"] = None
        changes["pending_changes"] = None
        changes["pending_by"] = None
        changes["approval_id"] = None
        await dccollection.update_one(
            {"contract_number": record.get("contract_number")},
            {"$set": changes},
        )
        await aprcollection.update_one(
            {"approval_id": approval_id},
            {"$set": {"status": "approved", "resolved_at": datetime.now().isoformat()}},
        )
        return {"message": "Semua setuju. Perubahan kontrak berhasil diterapkan."}

    if approval_type == "rule_catalog_create":
        # Cek konflik code baru terhadap katalog saat ini — bila admin sempat
        # membuat modul dengan code sama setelah pengajuan diajukan, batalkan
        # apply supaya tidak ada duplikat (tanpa unique index DB).
        rule = record["proposed_changes"]
        code = rule.get("code") or record.get("target_id")
        existing = await catalogcollection.find_one({"code": code})
        if existing:
            await aprcollection.update_one(
                {"approval_id": approval_id},
                {"$set": {
                    "status": "rejected",
                    "resolved_at": datetime.now().isoformat(),
                    "rejection_reason": f"Modul dengan code '{code}' sudah ada di katalog saat pengajuan disetujui.",
                }},
            )
            raise HTTPException(
                status_code=409,
                detail=f"Modul '{code}' sudah ada di katalog. Pengajuan otomatis ditolak.",
            )
        await catalogcollection.insert_one(rule)
        await aprcollection.update_one(
            {"approval_id": approval_id},
            {"$set": {"status": "approved", "resolved_at": datetime.now().isoformat()}},
        )
        return {"message": f"Semua setuju. Modul '{code}' ditambahkan ke katalog."}

    # Unknown type — defensif, jangan biarkan approval nyangkut di pending.
    raise HTTPException(
        status_code=500,
        detail=f"Tipe approval '{approval_type}' tidak dikenal. Hubungi administrator.",
    )
