# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/ports.py
# # # Function: BaseModel Data Contract - Ports section
# # # =======================

from pydantic import BaseModel
from typing import List, Optional, Union

# # # ----------------------- Model Hierarchy
# # # Ports
# # #  |- PortsProperties
# # # ----------------------- Model Hierarchy

class PortsProperties(BaseModel):
    property: str
    value: Union[str, int]

class Ports(BaseModel):
    object: str
    properties: List[PortsProperties] # -> merujuk ke class PortsProperties