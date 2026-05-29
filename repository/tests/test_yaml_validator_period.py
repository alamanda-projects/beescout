"""Tests untuk strict period (effective_date/expiry_date) enforcement di YAML validator.

Spec BeeScout (data-contract/docs/README.md, standard_version 0.5.0):
keduanya wajib di top-level `metadata.*`. Validator menerima legacy
`metadata.sla.effective_date` & `metadata.sla.end_of_contract` sebagai
fallback (sebelum migrasi data lengkap), tapi tetap akan men-trigger error
kalau keduanya kosong di kedua lokasi.
"""

import io

import pytest


def _yaml_with_period(top_eff: str | None = None,
                      top_exp: str | None = None,
                      sla_eff: str | None = None,
                      sla_eoc: str | None = None) -> bytes:
    lines = [
        "standard_version: 1.0.0",
        "contract_number: CN-PERIOD",
        "metadata:",
        "  name: Test Contract",
        "  owner: Test Team",
        "  version: 1.0.0",
        "  type: CSV",
    ]
    if top_eff:
        lines.append(f"  effective_date: {top_eff}")
    if top_exp:
        lines.append(f"  expiry_date: {top_exp}")
    if sla_eff or sla_eoc:
        lines.append("  sla:")
        if sla_eff:
            lines.append(f"    effective_date: {sla_eff}")
        if sla_eoc:
            lines.append(f"    end_of_contract: {sla_eoc}")
    return ("\n".join(lines) + "\n").encode("utf-8")


@pytest.fixture
def override_token():
    from app.main import app
    from app.core.verificator import token_verification

    def _set():
        app.dependency_overrides[token_verification] = lambda: {
            "usr": "admin", "typ": "user", "lvl": "admin", "sts": True, "tim": "admin"
        }

    yield _set
    app.dependency_overrides.pop(token_verification, None)


def _period_errors(body: dict) -> list:
    return [e for e in body.get("errors", []) if e.get("field", "").startswith("metadata.eff") or e.get("field", "").startswith("metadata.exp")]


@pytest.mark.asyncio
async def test_validator_accepts_toplevel_period(client, override_token):
    """Shape baru: top-level metadata.effective_date + expiry_date diterima."""
    ac, _ = client
    override_token()
    file = io.BytesIO(_yaml_with_period(top_eff="2024-01-01", top_exp="2025-12-31"))
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("test.yaml", file, "application/x-yaml")},
    )
    assert res.status_code == 200, res.text
    assert _period_errors(res.json()) == []


@pytest.mark.asyncio
async def test_validator_accepts_legacy_sla_period(client, override_token):
    """Shape lama: metadata.sla.effective_date + end_of_contract masih diterima
    (Pydantic compat shim akan auto-promote)."""
    ac, _ = client
    override_token()
    file = io.BytesIO(_yaml_with_period(sla_eff="2024-01-01", sla_eoc="2025-12-31"))
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("test.yaml", file, "application/x-yaml")},
    )
    assert res.status_code == 200, res.text
    assert _period_errors(res.json()) == []


@pytest.mark.asyncio
async def test_validator_rejects_missing_both_period(client, override_token):
    """Tanpa effective_date & expiry_date di top-level maupun legacy → 2 errors."""
    ac, _ = client
    override_token()
    file = io.BytesIO(_yaml_with_period())
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("test.yaml", file, "application/x-yaml")},
    )
    assert res.status_code == 200, res.text
    errs = _period_errors(res.json())
    assert len(errs) == 2
    fields = {e["field"] for e in errs}
    assert fields == {"metadata.effective_date", "metadata.expiry_date"}


@pytest.mark.asyncio
async def test_validator_rejects_partial_period(client, override_token):
    """effective_date ada di top-level, expiry_date tidak ada di manapun → 1 error."""
    ac, _ = client
    override_token()
    file = io.BytesIO(_yaml_with_period(top_eff="2024-01-01"))
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("test.yaml", file, "application/x-yaml")},
    )
    assert res.status_code == 200, res.text
    errs = _period_errors(res.json())
    assert len(errs) == 1
    assert errs[0]["field"] == "metadata.expiry_date"
