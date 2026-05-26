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
    # UI aliases (#102): tidak ada di BeeScout spec — dipakai FE wizard untuk
    # convenience input. `availability` = string ringkas "99.9%"; `cron` =
    # alias `frequency_cron`. Konsolidasi ke field spec di Phase 2 PR-B.
    availability: Optional[str] = None
    cron: Optional[str] = None


class MetadataQualityCustom(BaseModel):
    property: Optional[str] = None
    value: Optional[Union[str, int]] = None


class MetadataQuality(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    dimension: Optional[str] = None
    impact: Optional[str] = None    # operational | financial | regulatory | reputational
    severity: Optional[str] = None  # low | medium | high
    custom_properties: Optional[
        List[MetadataQualityCustom]
    ] = None  # -> merujuk ke class MetadataQualityCustom


class MetadataStakeholders(BaseModel):
    name: str
    email: Optional[str] = None
    role: str
    # ADR-0004: referensi ke dgrusr.username — wajib agar stakeholder ini
    # dihitung sebagai approver. Tetap opsional untuk kompatibilitas kontrak lama.
    username: Optional[str] = None
    date_in: Optional[str] = None
    date_out: Optional[str] = None


class MetadataConsumer(BaseModel):
    name: Optional[str] = None
    use_case: Optional[str] = None


class MetadataContractReference(BaseModel):
    """Referensi kontrak eksternal (mis. nomor tiket permintaan data).
    Spec: List[{number, type}] di metadata.contract_reference. Sebelumnya
    di-type sebagai List[str] (bug, #102 PR-A)."""
    number: Optional[str] = None
    type: Optional[str] = None


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
    contract_reference: Optional[List[MetadataContractReference]] = None
