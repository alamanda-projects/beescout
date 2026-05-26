# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/exmaples.py
# # # Function: BaseModel Data Contract - Example section
# # # =======================

from pydantic import BaseModel
from typing import List, Optional, Union

# # # ----------------------- Model Hierarchy
# # # Examples
# # # ----------------------- Model Hierarchy


class Examples(BaseModel):
    # Pydantic v2: Optional butuh default value eksplisit (#102 PR-A).
    type: Optional[str] = None
    data: Optional[str] = None
