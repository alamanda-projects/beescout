# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/core/verificator.py
# # # Function: Password verificator
# # # =======================

from fastapi import HTTPException, Header, Depends, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.core.connection import database, col_dgr, col_usr
from app.core.hasher import Hasher
from app.info.app_info import usr_403, usr_401_unauth, usr_401_inact, dc_404
from decouple import config

# Database declaration
usrcollection = database[col_usr]
dccollection = database[col_dgr]

# Error response
usrincorect = usr_401_unauth
usrnotallowed = usr_403
usrnotactive = usr_401_inact
dcnotfound = dc_404
userincorrect = HTTPException(status_code=401, detail=usrincorect)
usr_401_cnvc = config("USR_401_CNVC")

# access level config
grplvlroot = ["root"]
grplvladmin = ["root", "admin"]
grplvlall = ["root", "admin", "user", "developer"]


async def user_verification(
    username: str = Header(..., title="Username"),
    password: str = Header(..., title="Password"),
):
    loginupass = password

    dbuser = await usrcollection.find_one({"username": username})

    if dbuser is None:
        raise userincorrect

    dbuname = dbuser["username"]
    dbupass = dbuser["password"]
    dbname = dbuser["name"]
    dblvl = dbuser["group_access"]
    dbteam = dbuser["data_domain"]
    dbuact = dbuser["is_active"]
    dbutype = dbuser["type"]

    if not dbuname:
        raise userincorrect

    if dbutype != "user":
        raise userincorrect

    if not Hasher.verify_password(loginupass, dbupass):
        raise userincorrect

    return {
        "username": dbuname,
        "name": dbname,
        "type": dbutype,
        "level": dblvl,
        "data_domain": dbteam,
        "is_active": dbuact,
    }


async def access_verification(user_level: str, user_status: bool, user_group: list):
    if user_level not in user_group:
        raise HTTPException(status_code=403, detail=usrnotallowed)
    elif not user_status:
        raise HTTPException(status_code=401, detail=usrnotactive)


async def access_verification_filter(
    user_uname: str,
    user_level: str,
    user_status: bool,
    user_group: list,
    user_team: list,
    user_client: str = None,
    contract_number: str = None,
):
    # # User validation
    if user_client is None:
        user_info = await usrcollection.find_one({"username": user_uname})
        is_active = user_info.get("is_active")
        user_id = user_info.get("username")
    else:
        user_info = await usrcollection.find_one({"client_id": user_client})
        is_active = user_info.get("is_active")
        user_id = user_info.get("client_id")

    if is_active == False:
        raise HTTPException(status_code=401, detail=usrnotactive)

    # # Level validation
    if user_level not in user_group:
        raise HTTPException(status_code=403, detail=usrnotallowed)
    elif not user_status:
        raise HTTPException(status_code=401, detail=usrnotactive)

    # # Data Contract validation
    dc_info = await dccollection.find_one({"contract_number": contract_number})

    if dc_info is None:
        raise HTTPException(status_code=404, detail=dcnotfound)

    # # Team validation
    dc_team = dc_info["metadata"]["consumer"]

    dc_team_member = []
    for team_member in dc_team:
        dc_team_member.append(team_member.get("name", None))

    if user_team not in dc_team_member and user_level not in grplvladmin:
        raise HTTPException(status_code=403, detail=usrnotallowed)

    return


# # Function to verify the token & sakey
# Dependency to get the token from the Authorization header
sa_key = config("SA_SECRET_KEY")
sa_tkn = config("SA_SECRET_TOKEN")
sa_alg = config("SA_ALGORITHM")
sa_exp = int(config("SA_ACCESS_TOKEN_EXPIRE_DAYS"))
sa_secret = sa_key + sa_tkn

tkn_key = config("TKN_SECRET_KEY")
tkn_tkn = config("TKN_SECRET_TOKEN")
tkn_alg = config("TKN_ALGORITHM")
tkn_exp = int(config("TKN_ACCESS_TOKEN_EXPIRE_MINUTES"))
tkn_secret = tkn_key + tkn_tkn

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="")


async def token_verification(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = token.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, sa_secret, algorithms=[sa_alg])
        return payload
    except jwt.PyJWTError:
        try:
            payload = jwt.decode(token, tkn_secret, algorithms=[tkn_alg])
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=401,
                detail=usr_401_cnvc,
                headers={"WWW-Authenticate": "Bearer"},
            )
