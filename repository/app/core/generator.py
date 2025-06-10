# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/core/generator.py
# # # Function: Generator of any key / token
# # # =======================

import nanoid
import jwt
from decouple import config
from datetime import datetime, timedelta

# # ======================= Contract Number Generator
# # 13 digit length
# # alphabet = 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz
code_range = config("CODE_RANGE")
code_length_str = config("CODE_LENGTH")


def cn_generator():
    try:
        code_length = int(code_length_str)
    except ValueError:
        code_length = 13

    code = nanoid.generate(code_range, code_length)
    return code


# # # ======================= Token
# # # ======================= Bagian ini untuk kebutuhan manajemen token

# Secret key to sign the token
tkn_key = config("TKN_SECRET_KEY")
tkn_tkn = config("TKN_SECRET_TOKEN")
tkn_alg = config("TKN_ALGORITHM")
tkn_exp = int(config("TKN_ACCESS_TOKEN_EXPIRE_MINUTES"))
tkn_secret = tkn_key + tkn_tkn


# Function to create a new JWT token
def create_jwt_token(data: dict, expires_delta: int):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire, "iss": "BeeScout", "typ": "user"})
    encoded_jwt = jwt.encode(to_encode, tkn_secret, algorithm=tkn_alg)
    return encoded_jwt


def create_jwt_token_sakey(data: dict, expires_delta: int):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire, "iss": "BeeScout", "typ": "sa"})
    encoded_jwt = jwt.encode(to_encode, sa_secret, algorithm=sa_alg)
    return encoded_jwt


# # # ======================= Service Account Key (SA-Key)
# # # ======================= Bagian ini untuk kebutuhan manajemen SA-Key
sa_key = config("SA_SECRET_KEY")
sa_tkn = config("SA_SECRET_TOKEN")
sa_alg = config("SA_ALGORITHM")
sa_exp = int(config("SA_ACCESS_TOKEN_EXPIRE_DAYS"))
sa_secret = sa_key + sa_tkn


# Function to create a new private key
def create_private_key(data: dict, expires_delta: int):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=expires_delta)
    to_encode.update({"exp": expire, "iss": "BeeScout", "typ": "user"})
    encoded_jwt = jwt.encode(to_encode, sa_secret, algorithm=sa_alg)
    return encoded_jwt
