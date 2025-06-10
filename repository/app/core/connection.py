# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/core/connection.py
# # # Function: Connection to any databases / storages
# # # =======================

from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config

host = config("MONGODB_HOST", default="dgr-db")
user = config("MONGODB_USER", default="admin")
password = config("MONGODB_PASS", default="yellow")
port = config("MONGODB_PORT", default="27017")
db = config("MONGODB_DB", default="dgrdb")
col_dgr = config("MONGODB_COLLECTION_DGR", default="dgr")
col_usr = config("MONGODB_COLLECTION_USR", default="dgrusr")
# db_usr = config("MONGODB_DB_USR")

string_connection = f"mongodb://{user}:{password}@{host}:{port}/"
client = AsyncIOMotorClient(string_connection)
database = client[db]
# database_usr = client[db_usr]
