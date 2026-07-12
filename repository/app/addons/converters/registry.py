"""
Registry converter add-on — auto-discovery modul di folder ini (#154).

Setiap modul converter (odcs.py, sling.py, ...) mengekspor instance
`base.Converter` bernama `CONVERTER`. Registry memindai package sekali
(lazy, di-cache) sehingga menambah converter = menambah satu file.
"""
from __future__ import annotations

import importlib
import pkgutil

from app.addons import converters as _pkg
from app.addons.converters.base import Converter

# Modul infrastruktur yang bukan converter.
_SKIP_MODULES = {"base", "registry"}

_registry: dict[str, Converter] | None = None


def _discover() -> dict[str, Converter]:
    found: dict[str, Converter] = {}
    for mod_info in pkgutil.iter_modules(_pkg.__path__):
        if mod_info.name in _SKIP_MODULES or mod_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{_pkg.__name__}.{mod_info.name}")
        conv = getattr(module, "CONVERTER", None)
        if not isinstance(conv, Converter):
            # Modul tanpa CONVERTER valid di-skip diam-diam supaya file helper
            # tetap boleh hidup di folder ini.
            continue
        if conv.format_id in found:
            raise ValueError(
                f"Converter duplikat untuk format_id '{conv.format_id}' "
                f"(modul {mod_info.name})."
            )
        found[conv.format_id] = conv
    return found


def all_converters() -> dict[str, Converter]:
    """Semua converter ter-registrasi, keyed by format_id (cached)."""
    global _registry
    if _registry is None:
        _registry = _discover()
    return _registry


def get_converter(format_id: str) -> Converter | None:
    return all_converters().get(format_id)


def available_formats() -> list[str]:
    return sorted(all_converters().keys())
