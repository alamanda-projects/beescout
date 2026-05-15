# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/rule_catalog.py
# # # Function: BaseModel for Rule Catalog (modular quality rules)
# # # =======================

from pydantic import BaseModel
from typing import List, Optional, Literal


PARAM_TYPES = Literal["text", "number", "select", "multi", "date"]
LAYER_TYPES  = Literal["dataset", "column", "both"]
DIMENSION_TYPES = Literal["completeness", "validity", "accuracy", "security"]
IMPACT_TYPES = Literal["operational", "high", "low"]


class RuleParamOption(BaseModel):
    """Opsi dropdown untuk parameter bertipe select/multi."""
    value: str
    label: str


class RuleParam(BaseModel):
    """
    Satu parameter yang perlu diisi user saat memilih aturan ini.
    Schema ini menentukan input apa yang muncul di sentence builder.
    """
    key: str                                    # nama key di custom_properties YAML
    label: str                                  # label bahasa Indonesia untuk user bisnis
    type: PARAM_TYPES                           # tipe input
    required: bool = True
    options: Optional[List[RuleParamOption]] = None   # untuk type=select/multi
    min_value: Optional[float] = None           # validasi: nilai minimum (type=number/date)
    max_value: Optional[float] = None           # validasi: nilai maksimum (type=number/date)
    hint: Optional[str] = None                  # teks bantuan di bawah input


class RuleCatalogItem(BaseModel):
    """
    Satu modul aturan kualitas dalam katalog.
    Modul built-in tidak bisa dihapus (is_builtin=True).
    """
    code: str                                   # kode teknis: null_check, format_check, dll.
    label: str                                  # nama bahasa Indonesia: "Tidak Boleh Kosong"
    description: Optional[str] = None          # deskripsi singkat untuk user bisnis
    layer: LAYER_TYPES                          # berlaku di: dataset | column | both
    dimension: DIMENSION_TYPES                  # completeness | validity | accuracy | security
    sentence_template: str                      # template kalimat dengan {placeholder}
    params: List[RuleParam] = []               # schema parameter yang perlu diisi
    is_builtin: bool = True                     # modul bawaan tidak bisa dihapus
    is_active: bool = True


class RuleCatalogCreate(BaseModel):
    """Payload untuk membuat modul baru (POST /catalog/rules)."""
    code: str
    label: str
    description: Optional[str] = None
    layer: LAYER_TYPES
    dimension: DIMENSION_TYPES
    sentence_template: str
    params: List[RuleParam] = []


class RuleCatalogUpdate(BaseModel):
    """Payload untuk update modul kustom (PATCH /catalog/rules/{code})."""
    label: Optional[str] = None
    description: Optional[str] = None
    sentence_template: Optional[str] = None
    params: Optional[List[RuleParam]] = None
    is_active: Optional[bool] = None

