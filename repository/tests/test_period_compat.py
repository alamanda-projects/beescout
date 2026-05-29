"""
Tests untuk compat shim Metadata.effective_date / expiry_date (#103).

Cek bahwa payload lama dengan `sla.effective_date` / `sla.end_of_contract`
otomatis di-promote ke top-level oleh Pydantic model_validator.
"""

from app.model.metadata import Metadata


def _base_metadata(**overrides) -> dict:
    """Metadata minimal yang valid (4 required field), lalu di-override."""
    base = {
        "version": "1.0.0",
        "type": "CSV",
        "name": "customer list",
        "owner": "marketing",
    }
    base.update(overrides)
    return base


# ── Compat: legacy payload (sla.*) ────────────────────────────────────────────


def test_legacy_sla_fields_promoted_to_toplevel():
    """Payload lama dengan effective_date & end_of_contract di sla.* di-promote
    ke top-level, dan field lama dihapus dari sla."""
    raw = _base_metadata(
        sla={
            "frequency": 4,
            "effective_date": "2024-01-01",
            "end_of_contract": "2025-12-31",
        },
    )
    m = Metadata.model_validate(raw)
    assert m.effective_date == "2024-01-01"
    assert m.expiry_date == "2025-12-31"
    # Field lama harus dibersihkan dari MetadataSla (kalau model masih
    # menyimpannya, getattr akan throw atau return None — keduanya ok).
    assert getattr(m.sla, "effective_date", None) is None
    assert getattr(m.sla, "end_of_contract", None) is None


def test_legacy_sla_only_one_field_promoted():
    """Hanya end_of_contract di legacy → expiry_date terisi, effective_date tetap None."""
    raw = _base_metadata(
        sla={"frequency": 4, "end_of_contract": "2025-12-31"},
    )
    m = Metadata.model_validate(raw)
    assert m.effective_date is None
    assert m.expiry_date == "2025-12-31"


# ── Top-level wins kalau ada konflik ─────────────────────────────────────────


def test_toplevel_value_wins_over_legacy_sla():
    """Kalau payload punya top-level effective_date *dan* sla.effective_date
    (campur), top-level menang & legacy sla.* tetap di-drop."""
    raw = _base_metadata(
        effective_date="2024-06-15",
        sla={"effective_date": "2023-01-01"},
    )
    m = Metadata.model_validate(raw)
    assert m.effective_date == "2024-06-15"


# ── New shape (top-level only) ────────────────────────────────────────────────


def test_new_shape_toplevel_only_works():
    """Payload baru langsung pakai top-level — shim tidak interfere."""
    raw = _base_metadata(
        effective_date="2024-01-01",
        expiry_date="2025-12-31",
        sla={"frequency": 4},
    )
    m = Metadata.model_validate(raw)
    assert m.effective_date == "2024-01-01"
    assert m.expiry_date == "2025-12-31"


# ── No sla at all ─────────────────────────────────────────────────────────────


def test_no_sla_block_at_all():
    """Kontrak tanpa sla langsung valid — tidak error di shim."""
    raw = _base_metadata(effective_date="2024-01-01", expiry_date="2025-12-31")
    m = Metadata.model_validate(raw)
    assert m.effective_date == "2024-01-01"
    assert m.expiry_date == "2025-12-31"
    assert m.sla is None


def test_empty_period_still_valid_pydantic_layer():
    """Pydantic masih Optional di PR-B (akan di-tighten di PR-C). Tidak boleh
    error walau tidak ada period field — agar FE wizard lama tetap bisa submit."""
    raw = _base_metadata()
    m = Metadata.model_validate(raw)
    assert m.effective_date is None
    assert m.expiry_date is None
