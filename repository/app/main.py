# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/main.py
# # # Function: Main script
# # # =======================

from fastapi import FastAPI, HTTPException, Depends, Request, Body, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Dict
from app.model.users import UserCreate
from app.core.connection import database, col_usr, col_dgr, col_apr
from app.model.rule_catalog import RuleCatalogCreate, RuleCatalogUpdate, BUILTIN_RULES
from app.model.approval import ApprovalRecord, VoteRequest
from app.core.display import *
from app.core.hasher import Hasher
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
    allow_methods=["GET", "POST"],
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


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "version": app_version}


@app.get("/setup/status", tags=["system"])
async def setup_status():
    """Returns whether the initial root account has been created."""
    existing_root = await usrcollection.find_one({"group_access": "root", "is_active": True})
    return {"setup_complete": existing_root is not None}


@app.post("/setup", tags=["system"])
async def bootstrap_setup(user_form: UserCreate):
    """
    One-time setup endpoint to create the first root account.
    Returns 409 if a root account already exists.
    This endpoint is disabled once setup is complete.
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
    user_data = {
        "username": user_form.username,
        "password": hashed_password,
        "name": user_form.name,
        "group_access": "root",
        "data_domain": user_form.data_domain,
        "is_active": True,
        "type": "user",
        "created_at": datetime.now(),
    }
    await usrcollection.insert_one(user_data)
    return {"message": "Root account created. Please log in and disable this endpoint in production."}


@app.on_event("startup")
async def seed_catalog():
    if await catalogcollection.count_documents({}) == 0:
        await catalogcollection.insert_many(BUILTIN_RULES)


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
    db_user = await usrcollection.find_one({"username": credentials["username"]})
    if not db_user:
        raise HTTPException(status_code=400, detail=random.choice(usrnotallowed))

    if not Hasher.verify_password(credentials["password"], db_user["password"]):
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
    await access_verification(user_level, user_status, grplvlall)
    # # checking access level

    if user_level not in grplvlall or user_status == False:
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
    cursor = usrcollection.find({}, {"_id": 0, "password": 0})
    users = await cursor.to_list(length=500)
    return users


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

    try:
        await dccollection.insert_one(payload)
        return {"message": "Insert Success"}
    except Exception as e:
        return {"error": str(e)}


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
            # Tentukan approvers: semua admin/root aktif + contract managers
            admin_users = await usrcollection.find(
                {"group_access": {"$in": grplvladmin}, "is_active": True},
                {"username": 1, "_id": 0}
            ).to_list(None)
            approvers = list({u["username"] for u in admin_users} | set(existing.get("managers") or []))

            from nanoid import generate
            approval_id = generate(size=16)

            approval_doc = {
                "approval_id": approval_id,
                "contract_number": contract_number,
                "requested_by": username,
                "proposed_changes": payload,
                "approvers": approvers,
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
    await catalogcollection.insert_many(BUILTIN_RULES)
    return {"message": f"{len(BUILTIN_RULES)} modul bawaan berhasil ditambahkan."}


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
async def create_rule(payload: RuleCatalogCreate, user=Depends(require_admin)):
    """
    Tambah modul aturan baru ke katalog (model patching).
    Hanya root dan admin.
    """
    existing = await catalogcollection.find_one({"code": payload.code})
    if existing:
        raise HTTPException(status_code=409, detail=f"Modul dengan code '{payload.code}' sudah ada.")

    doc = payload.model_dump()
    doc["is_builtin"] = False
    doc["is_active"] = True
    await catalogcollection.insert_one(doc)

    created = await catalogcollection.find_one({"code": payload.code}, {"_id": 0})
    return created


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

    if vote_data.vote == "rejected":
        await aprcollection.update_one(
            {"approval_id": approval_id},
            {"$set": {"status": "rejected", "resolved_at": datetime.now().isoformat()}},
        )
        await dccollection.update_one(
            {"contract_number": record["contract_number"]},
            {"$set": {"approval_status": "rejected", "pending_changes": None, "pending_by": None, "approval_id": None}},
        )
        return {"message": "Perubahan ditolak."}

    updated = await aprcollection.find_one({"approval_id": approval_id})
    approved_votes = [v for v in updated["votes"] if v["vote"] == "approved"]
    if len(approved_votes) == len(record["approvers"]):
        changes = record["proposed_changes"]
        changes.pop("contract_number", None)
        changes["approval_status"] = None
        changes["pending_changes"] = None
        changes["pending_by"] = None
        changes["approval_id"] = None
        await dccollection.update_one(
            {"contract_number": record["contract_number"]},
            {"$set": changes},
        )
        await aprcollection.update_one(
            {"approval_id": approval_id},
            {"$set": {"status": "approved", "resolved_at": datetime.now().isoformat()}},
        )
        return {"message": "Semua setuju. Perubahan berhasil diterapkan."}

    return {"message": "Vote diterima. Menunggu persetujuan anggota lain."}
