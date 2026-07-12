# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/model.py
# # # Function: BaseModel Data Contract - Model section
# # # =======================

from pydantic import BaseModel, model_validator
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
    # #151 / ADR-0008: tindakan engine saat rule gagal — abort | warn | skip |
    # quiet (level kolom boleh skip). Absen → fallback severity. Lenient read.
    on_failure: Optional[str] = None
    custom_properties: Optional[List[ModelQualityCustom]] = None  # -> merujuk ke class ModelQualityCustom


class Model(BaseModel):
    column: str
    business_name: Optional[str] = None
    logical_type: Optional[str] = None
    physical_type: Optional[str] = None
    # Boolean flags wajib di spec (lihat data-contract/docs/README.md).
    # Phase 2 PR-B #102: required dengan safe defaults — zero-breakage karena
    # default = nilai natural saat field tidak ada di kontrak lama. POST tanpa
    # field → default applied; POST dengan null → 422 (mencegah null leak).
    is_primary: bool = False
    is_nullable: bool = True       # konvensi DB — kolom default nullable
    is_partition: bool = False
    is_clustered: bool = False
    is_pii: bool = False
    is_audit: bool = False
    # is_mandatory masih ❓ Needs decision (potensial duplikatif dgn is_nullable
    # — lihat docs/pydantic-spec-audit.md). Tetap Optional sampai keputusan.
    is_mandatory: Optional[bool] = None
    description: Optional[str] = None
    quality: Optional[List[ModelQuality]] = None
    sample_value: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_none_bools(cls, data):
        """Lenient-read: kontrak legacy di MongoDB bisa punya None untuk field
        bool (sebelum PR #118 expose is_*). Coerce ke safe default sebelum
        Pydantic validasi supaya display path tidak crash (#bug: 500 on
        GET /datacontract/filter)."""
        if not isinstance(data, dict):
            return data
        BOOL_DEFAULTS = {
            "is_primary": False,
            "is_nullable": True,
            "is_partition": False,
            "is_clustered": False,
            "is_pii": False,
            "is_audit": False,
        }
        for field, default in BOOL_DEFAULTS.items():
            if data.get(field) is None:
                data[field] = default
        return data
