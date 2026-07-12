"""
Kontrak (protocol) untuk converter add-on (#154).

Satu converter = satu format eksternal. Modul converter mengekspor instance
`Converter` bernama `CONVERTER`; registry (registry.py) menemukannya otomatis.

Fungsi murni: `export_fn` / `import_fn` hanya menerima dan mengembalikan
data — tidak menyentuh database, request, atau state global.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

# export: dict kontrak BeeScout → string (isi file siap unduh).
ExportFn = Callable[[dict], str]
# import: dict hasil parse file eksternal → (dict kontrak BeeScout, warnings).
# Caller (endpoint) yang memvalidasi hasilnya via Pydantic / YAML validator.
ImportFn = Callable[[dict], tuple[dict, list[str]]]


@dataclass(frozen=True)
class Converter:
    """Deskriptor satu format converter.

    format_id       : id unik dipakai di query param `format=` (lowercase).
    label           : nama tampilan untuk UI/daftar.
    file_extension  : ekstensi file export, tanpa titik depan (mis. "odcs.yaml").
    media_type      : Content-Type respons export.
    export_fn       : None bila format ini import-only.
    import_fn       : None bila format ini export-only.
    """
    format_id: str
    label: str
    file_extension: str
    media_type: str = "application/yaml"
    export_fn: Optional[ExportFn] = None
    import_fn: Optional[ImportFn] = None

    @property
    def can_export(self) -> bool:
        return self.export_fn is not None

    @property
    def can_import(self) -> bool:
        return self.import_fn is not None

    def describe(self) -> dict:
        """Representasi untuk GET /converters."""
        return {
            "format_id": self.format_id,
            "label": self.label,
            "file_extension": self.file_extension,
            "can_export": self.can_export,
            "can_import": self.can_import,
        }
