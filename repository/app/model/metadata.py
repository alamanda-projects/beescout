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
    availability_start: Optional[int] = None
    availability_end: Optional[int] = None
    availability_unit: Optional[str] = None
    frequency: Optional[int] = None
    frequency_unit: Optional[str] = None
    frequency_cron: Optional[str] = None
    retention: Optional[int] = None
    retention_unit: Optional[str] = None
    effective_date: Optional[str] = None
    end_of_contract: Optional[str] = None
    availability: Optional[str] = None
    cron: Optional[str] = None


class MetadataQualityCustom(BaseModel):
    property: Optional[str]
    value: Optional[Union[str, int]]


class MetadataQuality(BaseModel):
    code: Optional[str]
    description: Optional[str]
    dimension: Optional[str]
    impact: Optional[str]    # operational | financial | regulatory | reputational
    severity: Optional[str] = None  # low | medium | high
    custom_properties: Optional[
        List[MetadataQualityCustom]
    ]  # -> merujuk ke class MetadataQualityCustom


class MetadataStakeholders(BaseModel):
    name: str
    email: Optional[str]
    role: str
    date_in: Optional[str]
    date_out: Optional[str]


class MetadataConsumer(BaseModel):
    name: Optional[str]
    use_case: Optional[str]


class MetadataDescription(BaseModel):
    purpose: Optional[str] = None
    usage: Optional[str] = None


class Metadata(BaseModel):
    version: str
    type: str
    name: str
    owner: str
    consumption_mode: Optional[str] = None
    description: Optional[MetadataDescription] = None
    consumer: Optional[List[MetadataConsumer]] = None
    stakeholders: Optional[List[MetadataStakeholders]] = None
    quality: Optional[List[MetadataQuality]] = None
    sla: Optional[MetadataSla] = None
    prev_contract: Optional[str] = None
    contract_reference: Optional[List[str]] = None
