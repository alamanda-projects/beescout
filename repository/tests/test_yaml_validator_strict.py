"""Tests untuk strict YAML validator — #102 Phase 3.

Memverifikasi bahwa /contracts/validate-yaml dan /contracts/import-yaml
menolak YAML yang melanggar enforcement yang sama dengan write-path
(/datacontract/add & /update):
  - metadata.description.purpose + usage wajib (#102 PR-B slice 1)
  - stakeholders[].email wajib (#102 PR-B slice 2)
  - minimal 1 stakeholder consumer/producer (ADR-0007)
  - model[].logical_type + physical_type + description wajib (#102 PR-B slices 3+4)
"""

import io

import pytest


# ─── Helpers ────────────────────────────────────────────────────────────────

def _minimal_yaml(
    *,
    description: dict | None = None,
    stakeholders: list | None = None,
    model: list | None = None,
) -> bytes:
    """YAML base yang semua field wajib terisi kecuali yang di-override."""
    desc = description if description is not None else {
        "purpose": "Untuk analisis penjualan",
        "usage": "private",
    }
    sh = stakeholders if stakeholders is not None else [
        {"name": "Tim Sales", "role": "consumer",
         "email": "tim@example.com", "date_in": "2024-01-01"},
    ]
    mdl = model if model is not None else []

    import yaml as _yaml

    doc: dict = {
        "standard_version": "1.0.0",
        "contract_number": "CN-STRICT-TEST",
        "metadata": {
            "name": "Test Kontrak",
            "owner": "Tim Test",
            "version": "1.0.0",
            "type": "CSV",
            "effective_date": "2024-01-01",
            "expiry_date": "2025-12-31",
        },
        "model": mdl,
        "ports": [],
    }
    if desc:
        doc["metadata"]["description"] = desc
    if sh is not None:
        doc["metadata"]["stakeholders"] = sh

    return _yaml.dump(doc, allow_unicode=True).encode("utf-8")


@pytest.fixture
def admin_bypass(client):
    from app.main import app, require_admin

    _, mocks = client
    mocks["dgr"].reset_mock()

    async def fake_admin():
        return {"usr": "admin", "lvl": "admin", "sts": True}

    app.dependency_overrides[require_admin] = fake_admin
    yield
    app.dependency_overrides.clear()


# ─── validate-yaml ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_accepts_complete_yaml(client, admin_bypass):
    """YAML lengkap → valid: true, no errors."""
    ac, _ = client
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("ok.yaml", io.BytesIO(_minimal_yaml()), "text/yaml")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("valid") is True, body.get("errors")


@pytest.mark.asyncio
async def test_validate_rejects_missing_description_purpose(client, admin_bypass):
    """description.purpose kosong → error."""
    ac, _ = client
    payload = _minimal_yaml(description={"purpose": "", "usage": "private"})
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    fields = [e["field"] for e in body.get("errors", [])]
    assert "metadata.description.purpose" in fields


@pytest.mark.asyncio
async def test_validate_rejects_missing_description_usage(client, admin_bypass):
    """description.usage kosong → error."""
    ac, _ = client
    payload = _minimal_yaml(description={"purpose": "Analisis", "usage": ""})
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    fields = [e["field"] for e in body.get("errors", [])]
    assert "metadata.description.usage" in fields


@pytest.mark.asyncio
async def test_validate_rejects_stakeholder_missing_email(client, admin_bypass):
    """Stakeholder ber-name tanpa email → error."""
    ac, _ = client
    sh = [{"name": "Tim Sales", "role": "consumer", "date_in": "2024-01-01"}]
    payload = _minimal_yaml(stakeholders=sh)
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    fields = [e["field"] for e in body.get("errors", [])]
    assert "metadata.stakeholders[0].email" in fields


@pytest.mark.asyncio
async def test_validate_rejects_no_consumer_producer_stakeholder(client, admin_bypass):
    """Tidak ada stakeholder consumer/producer → error."""
    ac, _ = client
    sh = [{"name": "Pak X", "role": "owner",
           "email": "x@example.com", "date_in": "2024-01-01"}]
    payload = _minimal_yaml(stakeholders=sh)
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    fields = [e["field"] for e in body.get("errors", [])]
    assert "metadata.stakeholders" in fields


@pytest.mark.asyncio
async def test_validate_rejects_column_missing_logical_type(client, admin_bypass):
    """Kolom tanpa logical_type → error."""
    ac, _ = client
    mdl = [{"column": "id", "physical_type": "VARCHAR(36)", "description": "Primary key"}]
    payload = _minimal_yaml(model=mdl)
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    fields = [e["field"] for e in body.get("errors", [])]
    assert "model[0].logical_type" in fields


@pytest.mark.asyncio
async def test_validate_rejects_column_missing_physical_type(client, admin_bypass):
    """Kolom tanpa physical_type → error."""
    ac, _ = client
    mdl = [{"column": "id", "logical_type": "UUID", "description": "Primary key"}]
    payload = _minimal_yaml(model=mdl)
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    fields = [e["field"] for e in body.get("errors", [])]
    assert "model[0].physical_type" in fields


@pytest.mark.asyncio
async def test_validate_rejects_column_missing_description(client, admin_bypass):
    """Kolom tanpa description → error."""
    ac, _ = client
    mdl = [{"column": "id", "logical_type": "UUID", "physical_type": "VARCHAR(36)"}]
    payload = _minimal_yaml(model=mdl)
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    fields = [e["field"] for e in body.get("errors", [])]
    assert "model[0].description" in fields


@pytest.mark.asyncio
async def test_validate_accepts_complete_column(client, admin_bypass):
    """Kolom lengkap (logical + physical + description) → tidak ada model error."""
    ac, _ = client
    mdl = [{"column": "id", "logical_type": "UUID",
            "physical_type": "VARCHAR(36)", "description": "Identifier unik"}]
    payload = _minimal_yaml(model=mdl)
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    body = res.json()
    model_errors = [e for e in body.get("errors", []) if e["field"].startswith("model[")]
    assert model_errors == [], model_errors


# ─── import-yaml ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_rejects_missing_description(client, admin_bypass):
    """import-yaml: description kosong → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    payload = _minimal_yaml(description={"purpose": "", "usage": "private"})
    res = await ac.post(
        "/contracts/import-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    assert res.status_code == 422
    assert "description" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_import_rejects_stakeholder_missing_date_in(client, admin_bypass):
    """import-yaml: stakeholder ber-name tanpa date_in → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    sh = [{"name": "Tim Sales", "role": "consumer", "email": "s@example.com"}]
    payload = _minimal_yaml(stakeholders=sh)
    res = await ac.post(
        "/contracts/import-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    assert res.status_code == 422
    assert "date_in" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_import_rejects_stakeholder_missing_email(client, admin_bypass):
    """import-yaml: stakeholder ber-name tanpa email → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    sh = [{"name": "Tim Sales", "role": "consumer", "date_in": "2024-01-01"}]
    payload = _minimal_yaml(stakeholders=sh)
    res = await ac.post(
        "/contracts/import-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    assert res.status_code == 422
    assert "email" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_import_rejects_column_missing_types_and_description(client, admin_bypass):
    """import-yaml: kolom tanpa logical_type/physical_type/description → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mdl = [{"column": "id"}]
    payload = _minimal_yaml(model=mdl)
    res = await ac.post(
        "/contracts/import-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    assert res.status_code == 422
    assert "logical_type" in res.json()["detail"] or "physical_type" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_import_accepts_complete_yaml(client, admin_bypass):
    """import-yaml: YAML lengkap (dengan kolom) → 201."""
    ac, mocks = client
    mocks["dgr"].find_one.side_effect = [None, {"contract_number": "CN-STRICT-TEST"}]
    mdl = [{"column": "id", "logical_type": "UUID",
            "physical_type": "VARCHAR(36)", "description": "Identifier unik"}]
    payload = _minimal_yaml(model=mdl)
    res = await ac.post(
        "/contracts/import-yaml",
        files={"file": ("t.yaml", io.BytesIO(payload), "text/yaml")},
    )
    assert res.status_code == 201, res.text
    mocks["dgr"].insert_one.assert_awaited_once()
