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
    property: Optional[str] = None
    value: Optional[Union[str, int]] = None


class ModelQuality(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    dimension: Optional[str] = None
    impact: Optional[str] = None    # operational | financial | regulatory | reputational
    severity: Optional[str] = None  # low | medium | high
    custom_properties: Optional[List[ModelQualityCustom]] = None  # -> merujuk ke class ModelQualityCustom


class Model(BaseModel):
    column: str
    business_name: Optional[str] = None
    logical_type: Optional[str] = None
    physical_type: Optional[str] = None
    is_primary: Optional[bool] = None
    is_nullable: Optional[bool] = None
    is_partition: Optional[bool] = None
    is_clustered: Optional[bool] = None
    is_pii: Optional[bool] = None
    is_audit: Optional[bool] = None
    is_mandatory: Optional[bool] = None
    description: Optional[str] = None
    quality: Optional[List[ModelQuality]] = None
    sample_value: Optional[List[str]] = None
    tags: Optional[List[str]] = None
