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
# # #  |  |- ModelQualityCustom
# # #  |- ModelSemantic
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


# #162 / ADR-0009: enum klasifikasi semantik. Didefinisikan di sini (bukan di
# main.py) supaya converter add-on bisa ikut memakainya tanpa circular import —
# pola yang sama dengan DIMENSION_TYPES di rule_catalog.py.
SEMANTIC_CLASSIFICATIONS = ("public", "internal", "confidential", "sensitive", "pii")
# Nilai yang menyiratkan data pribadi — dasar derivasi satu arah ke `is_pii`.
PII_CLASSIFICATIONS = ("pii", "sensitive")


class ModelSemantic(BaseModel):
    """#162 / ADR-0009: metadata bisnis machine-readable per kolom.

    Melengkapi `description` (free-text untuk manusia), tidak menggantikannya.
    Seluruh properti opsional — kontrak tanpa blok `semantic` tetap valid
    tanpa migration. `entity` + `concept` membentuk identitas konsep
    (mis. "Customer.Identifier") yang bisa dicocokkan lintas kontrak.
    """
    entity: Optional[str] = None       # entitas bisnis, mis. Customer
    concept: Optional[str] = None      # makna di dalam entitas, mis. Identifier
    canonical: Optional[bool] = None   # dokumentatif — tanpa registry, tidak ditegakkan
    glossary: Optional[str] = None     # referensi glosarium, tidak divalidasi di fase ini
    # public | internal | confidential | sensitive | pii — strict-write/lenient-read
    # (pola ADR-0008): enum ditegakkan di write-path main.py, di sini tetap
    # Optional[str] agar dokumen lama bernilai asing tidak bikin read path 500.
    classification: Optional[str] = None


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
    # #162 / ADR-0009 — blok opsional, additive. `semantic.classification`
    # tidak menggantikan `is_pii`; lihat aturan derivasi di converter ODCS.
    semantic: Optional[ModelSemantic] = None
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
