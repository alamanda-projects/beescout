"""
Tests untuk Phase 2 PR-B #102: model.is_* booleans required dengan safe
defaults. Zero-breakage karena default = nilai natural untuk kontrak lama.
"""

import pytest

from app.model.model import Model


# ── Backward compat: kontrak lama tanpa field is_* ────────────────────────────


def test_load_column_without_bool_fields_applies_defaults():
    """Kontrak lama disimpan tanpa is_* fields → load dengan defaults."""
    col = Model(column="user_id")
    assert col.is_primary is False
    assert col.is_nullable is True
    assert col.is_partition is False
    assert col.is_clustered is False
    assert col.is_pii is False
    assert col.is_audit is False
    # is_mandatory masih Optional (❓ pending konsolidasi dgn is_nullable)
    assert col.is_mandatory is None


def test_load_column_with_partial_bool_fields():
    """Kontrak dengan sebagian field is_* → tidak override yang sudah ada."""
    col = Model(column="email", is_pii=True, is_nullable=False)
    assert col.is_pii is True
    assert col.is_nullable is False
    # field lain pakai default
    assert col.is_primary is False
    assert col.is_partition is False


# ── New contract: POST dengan bool eksplisit ──────────────────────────────────


def test_load_column_all_bool_explicit():
    col = Model(
        column="id",
        is_primary=True,
        is_nullable=False,
        is_partition=True,
        is_clustered=True,
        is_pii=False,
        is_audit=False,
    )
    assert col.is_primary is True
    assert col.is_nullable is False
    assert col.is_partition is True
    assert col.is_clustered is True


# ── Lenient-read: None di-coerce ke safe default (bukan rejected) ─────────────
# Pola codebase: FE zod yang cegah null dikirim; Pydantic lenient-read supaya
# kontrak legacy dengan None di MongoDB tetap bisa di-baca (bug 500 fix).


def test_none_coerced_to_default_for_bool_fields():
    """None dari MongoDB legacy → di-coerce ke default, tidak ValidationError."""
    col = Model(column="user_id", is_pii=None, is_partition=None)
    assert col.is_pii is False
    assert col.is_partition is False


# ── Round-trip: dump kembalikan field eksplisit ───────────────────────────────


def test_dump_includes_bool_defaults():
    """Saat di-serialize, field default ikut keluar (penting untuk migrasi
    incremental: kontrak yang ter-load → save ulang → field sekarang ada)."""
    col = Model(column="user_id")
    dumped = col.model_dump()
    assert dumped["is_primary"] is False
    assert dumped["is_nullable"] is True
    assert dumped["is_pii"] is False
