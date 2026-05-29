# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/metadata.py
# # # Function: BaseModel Data Contract - Metadata section
# # # =======================

from pydantic import BaseModel, model_validator
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
    # UI aliases (#102): tidak ada di BeeScout spec — dipakai FE wizard untuk
    # convenience input. `availability` = string ringkas "99.9%"; `cron` =
    # alias `frequency_cron`. Konsolidasi ke field spec di Phase 2 PR-B.
    availability: Optional[str] = None
    cron: Optional[str] = None
    # NB: `effective_date` & `end_of_contract` dipindah ke Metadata top-level
    # sebagai `effective_date` & `expiry_date` di standard_version 0.5.0 (#103).
    # Payload lama tetap diterima via Metadata.model_validator (auto-promote).


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
    # Lifecycle kontrak (#103, standard_version 0.5.0). PR-C tighten ke
    # required setelah FE wizard expose input. Compat shim di model_validator
    # auto-promote legacy `sla.effective_date` / `sla.end_of_contract` agar
    # API client lama tetap jalan.
    effective_date: str
    expiry_date: str
    prev_contract: Optional[str] = None
    contract_reference: Optional[List[MetadataContractReference]] = None

    @model_validator(mode="before")
    @classmethod
    def _promote_legacy_period(cls, data):
        """Backward-compat (#103): payload lama yang menaruh `effective_date`
        & `end_of_contract` di `sla.*` di-promote ke top-level sebelum
        validasi. Membuat FE/API client lama tetap bekerja sampai mereka
        update ke shape baru."""
        if not isinstance(data, dict):
            return data
        sla = data.get("sla")
        if not isinstance(sla, dict):
            return data
        if data.get("effective_date") in (None, "") and sla.get("effective_date"):
            data["effective_date"] = sla["effective_date"]
        if data.get("expiry_date") in (None, "") and sla.get("end_of_contract"):
            data["expiry_date"] = sla["end_of_contract"]
        sla.pop("effective_date", None)
        sla.pop("end_of_contract", None)
        return data
