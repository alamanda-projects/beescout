"""
Tests untuk compat shim & required Metadata.effective_date / expiry_date (#103).

PR-C: keduanya wajib di Pydantic top-level. Compat shim tetap aktif:
payload lama dengan `sla.effective_date` / `sla.end_of_contract` di-promote
ke top-level otomatis sebelum validasi.
"""

import pytest
from pydantic import ValidationError

from app.model.metadata import Metadata


def _base_metadata(**overrides) -> dict:
    """Metadata minimal yang valid (4 required field), lalu di-override.
    Sejak PR-C, effective_date & expiry_date juga wajib — caller perlu
    inject keduanya kecuali sedang menguji error path."""
    base = {
        "version": "1.0.0",
        "type": "CSV",
        "name": "customer list",
        "owner": "marketing",
        "effective_date": "2024-01-01",
        "expiry_date": "2025-12-31",
    }
    base.update(overrides)
    return base


# ── Compat: legacy payload (sla.*) ────────────────────────────────────────────


def test_legacy_sla_fields_promoted_to_toplevel():
    """Payload lama dengan effective_date & end_of_contract di sla.* di-promote
    ke top-level (dan field lama dihapus dari sla) — tanpa perlu top-level."""
    raw = {
        "version": "1.0.0", "type": "CSV", "name": "customer list", "owner": "marketing",
        "sla": {
            "frequency": 4,
            "effective_date": "2024-01-01",
            "end_of_contract": "2025-12-31",
        },
    }
    m = Metadata.model_validate(raw)
    assert m.effective_date == "2024-01-01"
    assert m.expiry_date == "2025-12-31"
    # Field lama harus dibersihkan dari MetadataSla.
    assert getattr(m.sla, "effective_date", None) is None
    assert getattr(m.sla, "end_of_contract", None) is None


def test_legacy_sla_only_one_field_errors_without_other():
    """Hanya end_of_contract di legacy → expiry_date terpromote, tapi
    effective_date kosong → required error (PR-C tighten)."""
    raw = {
        "version": "1.0.0", "type": "CSV", "name": "customer list", "owner": "marketing",
        "sla": {"frequency": 4, "end_of_contract": "2025-12-31"},
    }
    with pytest.raises(ValidationError) as exc:
        Metadata.model_validate(raw)
    msg = str(exc.value)
    assert "effective_date" in msg


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


def test_empty_period_now_raises_validation_error():
    """PR-C: keduanya wajib. Payload tanpa effective_date & expiry_date di
    manapun (top-level maupun legacy sla.*) harus gagal validasi."""
    raw = {
        "version": "1.0.0", "type": "CSV", "name": "customer list", "owner": "marketing",
    }
    with pytest.raises(ValidationError) as exc:
        Metadata.model_validate(raw)
    msg = str(exc.value)
    assert "effective_date" in msg
    assert "expiry_date" in msg
