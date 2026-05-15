"""
Add-on loader — membaca data seed eksternal dari folder `app/addons/`.

Add-on adalah data (bukan kode) yang dimuat ke database saat setup awal lewat
halaman /setup. Organisasi dapat mengganti file di folder ini sebelum fresh
install untuk membawa katalog aturan / kontrak contoh versi internal mereka
tanpa menyentuh kode aplikasi.
"""

import json
from pathlib import Path
from typing import List

from app.model.rule_catalog import RuleCatalogItem


ADDONS_DIR = Path(__file__).resolve().parents[1] / "addons"

DEFAULT_CATALOG_RULES_ADDON = ADDONS_DIR / "catalog_rules" / "default.json"
DEFAULT_SAMPLE_CONTRACTS_ADDON = ADDONS_DIR / "sample_contracts" / "default.json"


def _load_json_list(path: Path) -> list:
    with path.open("r", encoding="utf-8") as addon_file:
        data = json.load(addon_file)
    if not isinstance(data, list):
        raise ValueError(f"Add-on di {path} harus berupa list of dict.")
    return data


def load_catalog_rules_addon(path: Path = DEFAULT_CATALOG_RULES_ADDON) -> List[dict]:
    """Muat add-on katalog aturan kualitas; tiap entri divalidasi via Pydantic."""
    return [RuleCatalogItem(**rule).dict() for rule in _load_json_list(path)]


def load_sample_contracts_addon(path: Path = DEFAULT_SAMPLE_CONTRACTS_ADDON) -> List[dict]:
    """Muat add-on contoh kontrak. Struktur kontrak panjang dan sudah dijaga
    oleh endpoint create-contract, jadi loader hanya memastikan format list."""
    return _load_json_list(path)
