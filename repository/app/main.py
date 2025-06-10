# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/main.py
# # # Function: Main script
# # # =======================

from fastapi import FastAPI, HTTPException, Depends, Request, Body
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from typing import Dict
from app.model.users import UserCreate
from app.core.connection import database, col_usr, col_dgr
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
import random

current_dateTime = datetime.now()

# Database declaration
usrcollection = database[col_usr]
dccollection = database[col_dgr]

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
    docs_url=None,
    redoc_url=None,
)


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
async def login_for_access_token(credentials: dict = Body(...)):
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
        secure=True,
        samesite="Strict",
    )
    return response


@app.post("/login/midware", tags=["user"])
async def login_with_sakey(credentials: dict = Body(...)):
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
        secure=True,
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
    # # checking access level
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvladmin)
    # # checking access level

    try:
        dccollection.insert_one(data.dict())
        return {"message": "Insert Success"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/datacontract/lists", tags=["datacontract"])
async def get_datacontract(current_user: dict = Depends(token_verification)):
    # # checking access level
    user_level = current_user["lvl"]
    user_status = current_user["sts"]
    await access_verification(user_level, user_status, grplvladmin)
    # # checking access level

    dclist = await display_all()

    return dclist


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

    dcfilter = await display_all(contract_number)

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
