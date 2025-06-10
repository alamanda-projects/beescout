# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/users.py
# # # Function: BaseModel Data Contract - User creation
# # # =======================

from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union
import datetime
from email_validator import validate_email, EmailNotValidError

# # # ----------------------- Model Hierarchy
# # # CreateUser
# # # ----------------------- Model Hierarchy

# Model untuk data user lengkap
class UserCreate(BaseModel):
    username: str
    name: str
    password: str
    group_access: str
    data_domain: str
    is_active: bool
