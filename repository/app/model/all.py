# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/all.py
# # # Function: Main BaseModel Data Contract
# # # =======================

from pydantic import BaseModel
from typing import List, Optional, Union

from app.model.metadata import Metadata
from app.model.model import Model
from app.model.ports import Ports
from app.model.examples import Examples
from app.model.dbtschema import Dbtschemas


# # # ----------------------- Model Hierarchy
# # # All
# # #  |- Metadatas -> merujuk ke ./metadata.py
# # #  |- Models -> merujuk ke ./model.py
# # #  |- Ports -> merujuk ke ./ports.py
# # #  |- Examples -> merujuk ke ./examples.py
# # # ----------------------- Model Hierarchy


class All(BaseModel):
    standard_version: str
    contract_number: str
    metadata: Metadata  # -> merujuk ke ./metadata.py
    model: List[Model]  # -> merujuk ke ./model.py
    ports: List[Ports]  # -> merujuk ke ./ports.py
    examples: Examples  # -> merujuk ke ./examples.py


class Metadatas(BaseModel):
    standard_version: str
    contract_number: str
    metadata: Metadata  # -> merujuk ke ./metadata.py


class Models(BaseModel):
    standard_version: str
    contract_number: str
    model: List[Model]  # -> merujuk ke ./model.py


class Ports(BaseModel):
    standard_version: str
    contract_number: str
    ports: List[Ports]  # -> merujuk ke ./ports.py


class Examples(BaseModel):
    standard_version: str
    contract_number: str
    examples: Examples  # -> merujuk ke ./examples.py


class Dbtschema(BaseModel):
    standard_version: str
    contract_number: str
    examples: Examples  # -> merujuk ke ./dbtschema.py