# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/metadata.py
# # # Function: BaseModel Data Contract - Metadata section
# # # =======================

from pydantic import BaseModel
from typing import List, Optional, Union

# # # ----------------------- Model Hierarchy
# # # Metadata
# # #  |- MetadataDescription
# # #  |- MetadataConsumer
# # #  |- MetadataStakeholders
# # #  |- MetadataQuality
# # #     |- MetadataQualityCustom
# # #  |- MetadataSla
# # # ----------------------- Model Hierarchy


class MetadataSla(BaseModel):
    availability_start: int
    availability_end: int
    availability_unit: str
    frequency: int
    frequency_unit: str
    frequency_cron: Optional[str]
    retention: int
    retention_unit: str
    effective_date: str
    end_of_contract: str


class MetadataQualityCustom(BaseModel):
    property: Optional[str]
    value: Optional[Union[str, int]]


class MetadataQuality(BaseModel):
    code: Optional[str]
    description: Optional[str]
    dimension: Optional[str]
    impact: Optional[str]
    custom_properties: Optional[
        List[MetadataQualityCustom]
    ]  # -> merujuk ke class MetadataQualityCustom


class MetadataStakeholders(BaseModel):
    name: str
    email: str
    role: str
    date_in: str
    date_out: Optional[str]


class MetadataConsumer(BaseModel):
    name: Optional[str]
    use_case: Optional[str]


class MetadataDescription(BaseModel):
    purpose: Optional[str]
    usage: str


class Metadata(BaseModel):
    version: str
    type: str
    name: str
    owner: str
    consumption_mode: Optional[str]
    description: MetadataDescription  # -> merujuk ke class MetadataDescription
    consumer: Optional[List[MetadataConsumer]]  # -> merujuk ke class MetadataConsumer
    stakeholders: List[MetadataStakeholders]  # -> merujuk ke class MetadataStakeholders
    quality: Optional[List[MetadataQuality]]  # -> merujuk ke class MetadataQuality
    sla: MetadataSla  # -> merujuk ke class MetadataSla
