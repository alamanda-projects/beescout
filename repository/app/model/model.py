# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/model.py
# # # Function: BaseModel Data Contract - Model section
# # # =======================

from pydantic import BaseModel
from typing import List, Optional, Union

# # # ----------------------- Model Hierarchy
# # # Model
# # #  |- ModelQuality
# # #     |- ModelQualityCustom
# # # ----------------------- Model Hierarchy


class ModelQualityCustom(BaseModel):
    property: Optional[str]
    value: Optional[Union[str, int]]


class ModelQuality(BaseModel):
    code: Optional[str]
    description: Optional[str]
    dimension: Optional[str]
    impact: Optional[str]
    custom_properties: Optional[List[ModelQualityCustom]]  # -> merujuk ke class ModelQualityCustom


class Model(BaseModel):
    column: str
    business_name: Optional[str]
    logical_type: str
    physical_type: str
    is_primary: bool
    is_nullable: bool
    is_partition: bool
    is_clustered: bool
    is_pii: bool
    is_audit: bool
    is_mandatory: bool
    description: str
    quality: Optional[List[ModelQuality]]  # -> merujuk ke class ModelQuality
    sample_value: Optional[List[str]]
    tags: Optional[List[str]]
