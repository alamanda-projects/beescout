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


# ─── Default built-in modules ─────────────────────────────────────────────────
# Digunakan sebagai seed data saat collection kosong.

BUILTIN_RULES: List[dict] = [
    {
        "code": "distinct_check",
        "label": "Tidak Ada Data Ganda",
        "description": "Pastikan tidak ada duplikat pada kolom yang ditentukan",
        "layer": "dataset",
        "dimension": "completeness",
        "sentence_template": "Pastikan tidak ada data ganda pada kolom {field_name}",
        "params": [
            {
                "key": "field_name",
                "label": "Kolom yang harus unik",
                "type": "multi",
                "required": True,
                "hint": "Pilih satu atau lebih kolom",
            }
        ],
        "is_builtin": True,
        "is_active": True,
    },
    {
        "code": "count_check",
        "label": "Jumlah Baris Sesuai",
        "description": "Pastikan jumlah baris data tidak terlalu sedikit atau berlebih",
        "layer": "dataset",
        "dimension": "completeness",
        "sentence_template": "Pastikan jumlah baris memenuhi kondisi {field_condition}",
        "params": [
            {
                "key": "field_condition",
                "label": "Kondisi yang harus terpenuhi",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "is_nullable=false", "label": "Kolom wajib terisi"},
                    {"value": "is_audit=true", "label": "Kolom berstatus audit"},
                ],
            }
        ],
        "is_builtin": True,
        "is_active": True,
    },
    {
        "code": "pii_check",
        "label": "Data Sensitif Dilindungi",
        "description": "Pastikan kolom yang berisi PII sudah di-masking",
        "layer": "dataset",
        "dimension": "security",
        "sentence_template": "Pastikan data sensitif pada kolom {field_name} sudah dilindungi",
        "params": [
            {
                "key": "field_name",
                "label": "Kolom yang berisi data sensitif",
                "type": "multi",
                "required": True,
                "hint": "Kolom berlabel PII otomatis terdeteksi",
            }
        ],
        "is_builtin": True,
        "is_active": True,
    },
    {
        "code": "null_check",
        "label": "Tidak Boleh Kosong",
        "description": "Setiap baris wajib memiliki nilai pada kolom ini",
        "layer": "column",
        "dimension": "completeness",
        "sentence_template": "Pastikan kolom {column} tidak boleh kosong dibandingkan {compare_to}",
        "params": [
            {
                "key": "compare_to",
                "label": "Dibandingkan dengan",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "total dataset row", "label": "Jumlah total baris"},
                    {"value": "specific row count", "label": "Jumlah baris tertentu"},
                ],
            },
            {
                "key": "comparison_type",
                "label": "Tipe perbandingan",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "equal to", "label": "Harus sama persis"},
                    {"value": "less than", "label": "Boleh kurang dari"},
                ],
            },
        ],
        "is_builtin": True,
        "is_active": True,
    },
    {
        "code": "format_check",
        "label": "Format / Panjang Sesuai",
        "description": "Panjang atau pola nilai harus sesuai ketentuan",
        "layer": "column",
        "dimension": "validity",
        "sentence_template": "Pastikan kolom {column} panjangnya tepat {length} karakter",
        "params": [
            {
                "key": "length",
                "label": "Panjang karakter yang diharapkan",
                "type": "number",
                "required": True,
                "min_value": 1,
                "max_value": 65535,
                "hint": "Antara 1 – 65.535 karakter",
            }
        ],
        "is_builtin": True,
        "is_active": True,
    },
    {
        "code": "string_check",
        "label": "Hanya Berisi Teks",
        "description": "Nilai tidak boleh mengandung angka atau karakter khusus",
        "layer": "column",
        "dimension": "accuracy",
        "sentence_template": "Pastikan kolom {column} hanya berisi {contains_only}",
        "params": [
            {
                "key": "contains_only",
                "label": "Hanya boleh berisi",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "alphabet", "label": "Huruf saja"},
                    {"value": "numeric", "label": "Angka saja"},
                    {"value": "alphanumeric", "label": "Huruf dan angka"},
                ],
            }
        ],
        "is_builtin": True,
        "is_active": True,
    },
    {
        "code": "date_range_check",
        "label": "Rentang Tanggal Valid",
        "description": "Nilai tanggal harus berada dalam rentang yang disepakati",
        "layer": "column",
        "dimension": "accuracy",
        "sentence_template": "Pastikan tanggal pada kolom {column} antara {min_date} hingga {max_date}",
        "params": [
            {
                "key": "min_date",
                "label": "Tanggal paling awal",
                "type": "date",
                "required": False,
                "hint": "Format: YYYY-MM-DD",
            },
            {
                "key": "max_date",
                "label": "Tanggal paling akhir",
                "type": "date",
                "required": False,
                "hint": "Gunakan 'today' untuk hari ini",
            },
        ],
        "is_builtin": True,
        "is_active": True,
    },
]
